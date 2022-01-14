from os.path import isdir
import pandas as pd
import argparse
import os


def main():
    """Main function"""
    filePath = command_line_parser()
    fileList = file_processor(filePath)

    print()
    print(filePath)
    print(fileList)
    print()

    df = fileOpen(filePath, fileList)


def fileOpen(filePath, fileList):
    """Opens a file or directory of .csv files"""
    df = pd.DataFrame()
    for item in fileList:
        data = pd.read_csv(f"{filePath}/{item}")
        df2 = pd.DataFrame(
            data, columns=["Tenant UUID", "Hour", "Host Name", "Host Units"]
        )
        df = df.append(df2, ignore_index=True)

    df = df.rename(columns={"Host Units": "HHU"})

    # Drop the Summary Rows
    df = df.dropna()

    # Convert to date
    df["Hour"] = pd.to_datetime(df["Hour"], format="%Y-%m-%d %H:%M:%S")

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
    print(f"Here are the args: {args}")

    filePath = args.raw_data_file_or_folder

    print(filePath == "data/2021-1102_Rogers_Cohort_1.csv")

    print(f"The file path is: {filePath}")
    return filePath


def file_processor(filePath):
    """builds a list of the files to be processed"""
    print(f"file_processor: {filePath} of {type(filePath)}")
    fileList = []
    if os.path.isfile(filePath):
        filePath, fileName = os.path.split(filePath)
        fileList = [fileName]
    elif os.path.isdir(filePath):
        print("Adding all .csv files in directory")
        with os.scandir(filePath) as dirs:
            for entry in dirs:
                if entry.name.endswith(".csv"):
                    # print(entry.name)
                    fileList.append(entry.name)
        if len(fileList) == 0:
            raise Exception("No .csv files in this directory")
        # print(fileList)
    else:
        raise Exception("Couldn't find a valid file from the path provided")

    return fileList


if __name__ == "__main__":
    main()
