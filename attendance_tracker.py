from os.path import isdir
import pandas as pd
import argparse
import os
import simplelogging
import re

# Setup the logging
log = simplelogging.get_logger(
    logger_level=simplelogging.DEBUG,
    console=True,
    console_level=simplelogging.DEBUG,
    file_name="logs/log.log",
    file_level=simplelogging.DEBUG,
)

for _ in range(2):
    print()

log.info("Starting logging")


def main():
    """Main function"""

    filePath, is_processing_ms_teams_reports = command_line_parser()
    filePath, fileList = file_processor(filePath)

    # log the task parameters
    log.info("path: %s", filePath)
    log.info("files: %s", fileList)
    log.info(
        "Processing MeetingAttendanceReports: %s\n",
        is_processing_ms_teams_reports,
    )
    log.info("")

    if is_processing_ms_teams_reports:
        df = build_list_from_teams(filePath, fileList)
    else:
        df = build_simple_list(filePath, fileList)

    csvExport(filePath, df)


def build_list_from_teams(filePath, fileList):
    """Build an email list from a raw Teams attendance file"""

    df = pd.DataFrame()
    df["Email"] = ""

    for item in fileList:
        log.info("===== Processing %s ======", item)

        # for some reason some of these files are utf-8 and some are utf-16. Handle both.
        try:
            with open(f"{filePath}/{item}", "r", encoding="utf-8") as fp:
                current_file = fp.read()
            log.info("✅ Opened %s with utf-8 encoding.", item)
        except UnicodeDecodeError as error:
            log.error("Not utf-8, trying utf-16. %s", error)
            with open(f"{filePath}/{item}", "r", encoding="utf-16") as fp:
                current_file = fp.read()
            log.info("✅ Opened %s with utf-16 encoding.", item)
        except Exception as error:
            log.error("🛑 Can't process %s. Skipping this file. %s", error)
            pass

        # Get the session title
        regex = r"Title\t(.*)\n"
        matches = re.findall(regex, current_file)

        try:
            session_title = matches[0]
        except IndexError as error:
            log.error("🛑 %s is not a recognized Teams Attendance files. Skipped", item)
            continue

        log.info("Title: %s", session_title)

        # Get the session date
        regex = r"Meeting Start Time\t(\d+)/(\d+)/(\d+),"
        matches = re.findall(regex, current_file)
        # print(matches[0])
        date = f"{matches[0][2]}-{int(matches[0][0]):02}{int(matches[0][1]):02}"
        log.info("Session date: %s", date)

        # Get the email addresess
        regex = r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}"
        matches = re.findall(regex, current_file, re.IGNORECASE)

        # make lower case
        emails = [x.lower() for x in matches]
        emails.sort()
        # log.debug(emails)

        # remove duplicate emails
        log.debug("Original list is %d long.", len(emails))
        cleaned_emails = []
        for email in emails:
            # looking for user name matches (ignore domain)
            name = email.split("@")[0]

            if not re.search(rf"{name}", str(cleaned_emails), re.IGNORECASE):
                cleaned_emails.append(email)

        log.info("This file contains %d unique emails", len(cleaned_emails))

        # now add this to the df and do the same things as the other function

        df2 = pd.DataFrame(cleaned_emails, columns=["Email"])
        df2[date] = True

        # Append to the main df

        df = df.append(df2, ignore_index=True)
        log.info("[DF] After this round total length is: %d", len(df))
        log.info("")
        # return the info for the filename

    # Now lets merge this list down to remove duplicates
    df = df.groupby(["Email"]).max()
    df = df.fillna(False)

    # Last step, sort the columns
    df = df[sorted(df.columns)]
    log.info("")
    log.info("===== SUMMARY ======")
    log.info("After groupby there are %d unique emails", len(df))

    return df


def build_simple_list(filePath, fileList):
    """Opens a file or directory of .csv files"""
    df = pd.DataFrame()
    df["Email"] = ""
    for item in fileList:
        log.info("Processing %s", item)

        # get the col name from the file
        col_name = item.split("_")[0]

        try:
            data = pd.read_csv(f"{filePath}/{item}", names=["Email"])

            # get attendance for that day
            data[col_name] = True
            log.debug("New data file\n%s", data)

            df = df.append(data)

            log.info("End of this file pass.")

        except:
            log.error(
                "Couldn't make any sense out of %s. I'm going to skip this.", item
            )
            pass

    # Groupby email. Max will prefer True
    df = df.groupby(["Email"]).max()

    # First time attendees will have NaN for older sessions, set to false
    df = df.fillna(False)

    # sort the columns
    df = df[sorted(df.columns)]

    log.info("All done here, ready to send back %s emails", len(df))

    return df


def csvExport(filePath, df):
    """CSV Export & some summary statistics"""
    startDate = df.columns[0]
    endDate = df.columns[-1]
    log.info("Includes meetings between %s and %s", startDate, endDate)

    os.makedirs(f"{filePath}/results", exist_ok=True)
    fileName = f"attendance_from_{startDate}_to_{endDate}.csv"
    log.info("Results saved in: %s/results/%s", filePath, fileName)
    df.to_csv(f"{filePath}/results/{fileName}", index=True)


def command_line_parser():
    """Command line args parsing"""

    parser = argparse.ArgumentParser(description="Build an attendance list")

    parser.add_argument(
        "raw_data_file_or_folder",
        nargs="?",
        default="data/2021-1102_Customer_Cohort_1.csv",
        type=str,
        metavar="<raw-data-file>",
        help="Include a .csv of a folder containing .csv",
    )

    parser.add_argument(
        "-t",
        "--teams",
        action="store_true",
        default=False,
        help="Process unaltered MS Teams meetingAttendanceReport.csv files",
    )

    args = parser.parse_args()
    log.debug(f"Here are the args: {args}")

    filePath = args.raw_data_file_or_folder
    processing_meeting_Attendance_Reports = args.teams

    log.info(f"The file path is: {filePath}")

    return filePath, processing_meeting_Attendance_Reports


def file_processor(filePath):
    """builds a list of the files to be processed"""

    log.debug(f"file_processor: {filePath} of {type(filePath)}")

    fileList = []

    if os.path.isfile(filePath):
        log.debug("Single file")
        filePath, fileName = os.path.split(filePath)
        fileList = [fileName]
    elif os.path.isdir(filePath):
        log.info("Adding .csv files in %s", filePath)
        with os.scandir(filePath) as dirs:
            for entry in dirs:
                if entry.name.endswith(".csv"):
                    fileList.append(entry.name)
        if len(fileList) == 0:
            raise Exception("No .csv files in this directory")
    else:
        raise Exception("Couldn't find a valid file from the path provided")

    return filePath, fileList


if __name__ == "__main__":
    main()
