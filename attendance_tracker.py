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

for _ in range(15):
    print()

log.info("Starting logging")


def main():
    """Main function"""

    filePath, processing_meeting_attendance_reports = command_line_parser()
    filePath, fileList = file_processor(filePath)

    # log the task parameters
    log.info("path: %s", filePath)
    log.info("files: %s", fileList)
    log.info(
        "Processing MeetingAttendanceReports: %s",
        processing_meeting_attendance_reports,
    )

    if processing_meeting_attendance_reports:
        df = build_list_from_raw(filePath, fileList)
    else:
        df = build_simple_list(filePath, fileList)

    csvExport(filePath, df)

    # print(df)


def build_list_from_raw(filePath, fileList):
    """Build an email list from a raw Teams attendance file"""

    df = pd.DataFrame()
    df["Email"] = ""

    for item in fileList:
        log.info("Processing %s", item)

        # may need to add a try block here to try utf-16 as well. I seem to be seeing both encodings
        with open(f"{filePath}/{item}", "r", encoding="utf-8") as fp:
            curr_file = fp.read()

        # Get the session title
        regex = r"Title\t(.*)\n"
        matches = re.findall(regex, curr_file)
        session_title = matches[0]
        log.info("Title: %s", session_title)

        # Get the session date
        regex = r"Meeting Start Time\t(\d+)/(\d+)/(\d+),"
        matches = re.findall(regex, curr_file)
        print(matches[0])
        date = f"{matches[0][2]}-{int(matches[0][0]):02}{int(matches[0][1]):02}"
        log.info("Session dae: %s", date)

        # Get the email addresess
        regex = r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}"
        matches = re.findall(regex, curr_file, re.IGNORECASE)

        # make lower case
        emails = [x.lower() for x in matches]
        emails.sort()
        log.debug(emails)

        # remove duplicate emails
        log.info("Original list is %d long.", len(emails))
        cleaned_emails = []
        for email in emails:
            # looking for user name matches (ignore domain)
            name = email.split("@")[0]

            if not re.search(rf"{name}", str(cleaned_emails), re.IGNORECASE):
                cleaned_emails.append(email)

        log.info(
            "The cleaned and sorted email list is %d emails long and contains: %s",
            len(cleaned_emails),
            cleaned_emails,
        )

        # now add this to the df and do the same things as the other function
        # return the info for the filename

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

            log.info("End of this file pass. df to carry over\n%s", df)

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

    log.info("All done here, ready to send back:\n %s", df)

    return df


def csvExport(filePath, df):
    """CSV Export & some summary statistics"""
    startDate = df.columns[0]
    endDate = df.columns[-1]
    print(f"From: {startDate} to {endDate}")
    # df["Excess"] = df["Excess"].astype(int)
    # df["HHU"] = df["HHU"].astype(int)
    # if os.path.isdir(f"{filePath}/results") == False:
    os.makedirs(f"{filePath}/results", exist_ok=True)
    log.debug("Results in: %s", filePath)
    df.to_csv(f"{filePath}/results/list_{startDate}_to_{endDate}.csv", index=True)


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
        "-r",
        "--raw",
        action="store_true",
        default=False,
        help="Process unaltered meetingAttendanceReport.csv files",
    )

    # parser.add_argument("-hu", "--hostunits", required=True,
    #                     help="The account host unit limit")
    args = parser.parse_args()
    log.debug(f"Here are the args: {args}")

    filePath = args.raw_data_file_or_folder
    processing_meeting_Attendance_Reports = args.raw

    # assert filePath == "data/2021-1102_Customer_Cohort_1.csv"

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
                    # print(entry.name)x
                    fileList.append(entry.name)
        if len(fileList) == 0:
            raise Exception("No .csv files in this directory")
        # print(fileList)
    else:
        raise Exception("Couldn't find a valid file from the path provided")

    return filePath, fileList


if __name__ == "__main__":
    main()
