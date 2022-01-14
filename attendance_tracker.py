from os.path import isdir
import pandas as pd
import argparse
import os
import simplelogging

# Setup the logging
log = simplelogging.get_logger(
    logger_level=simplelogging.DEBUG,
    console=True,
    console_level=simplelogging.DEBUG,
    file_name="logs/log.log",
    file_level=simplelogging.DEBUG,
)
log.info("Starting logging")


def main():
    """Main function"""

    filePath = command_line_parser()
    filePath, fileList = file_processor(filePath)

    log.info("path: %s", filePath)
    log.info("files: %s", fileList)

    df = fileOpen(filePath, fileList)

    print(df)


def fileOpen(filePath, fileList):
    """Opens a file or directory of .csv files"""
    df = pd.DataFrame()
    df["Email"] = ""
    for item in fileList:
        col_name = item.split("_")[0]
        data = pd.read_csv(f"{filePath}/{item}", names=["Email"])
        # data =
        # log.debug("Data: %s", data)
        # df2 = pd.DataFrame(data, columns=["Email"])
        # log.debug("%s", df.dtypes)
        # new_df = df.assign(f"{col_name}"="Yes")
        data[f"{col_name}"] = True
        log.info(data)
        # df[f"{col_name}"] = ["Yes", "Yes", "Yes", "Yes"]

        print("******")
        for index, row in data.iterrows():
            print(row["Email"])

            if df["Email"].str.contains(row["Email"], regex=False).any():
                print("match")
                print(df.loc[df["Email"] == row["Email"]])
                (df.loc[df["Email"] == row["Email"]])[col_name] = True 
            else:
                print("NO MATCH")
                df = df.append(row)
        print("******")

        # df = df.append(data, ignore_index=True)

    # df["Email"] = df.groupby("Email")["2021-1102"].ffill()
    # df1 = df.groupby("Email").ffill().drop_duplicates()
    # log.info("GROUP IT:\n %s", df1)

    # df = df.rename(columns={"Host Units": "HHU"})

    # Drop the Summary Rows
    # df = df.dropna()

    # Convert to date
    # df["Hour"] = pd.to_datetime(df["Hour"], format="%Y-%m-%d %H:%M:%S")

    log.info("Dataframe:\n %s", df)

    return df


def csvExport(filePath, df):
    """CSV Export & some summary statistics"""
    startDate = df["Hour"][0].strftime("%Y-%m-%d")
    endDate = df["Hour"].iloc[-1].strftime("%Y-%m-%d")
    print(f"From: {startDate} to {endDate}")
    df["Excess"] = df["Excess"].astype(int)
    df["HHU"] = df["HHU"].astype(int)
    # if os.path.isdir(f"{filePath}/results") == False:
    os.makedirs(f"{filePath}/results", exist_ok=True)
    df.to_csv(
        f"{filePath}/results/hourly_hhu_{startDate}_to_{endDate}.csv", index=False
    )


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

    # parser.add_argument("-hu", "--hostunits", required=True,
    #                     help="The account host unit limit")
    args = parser.parse_args()
    log.debug(f"Here are the args: {args}")

    filePath = args.raw_data_file_or_folder

    # assert filePath == "data/2021-1102_Customer_Cohort_1.csv"

    log.info(f"The file path is: {filePath}")

    return filePath


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
