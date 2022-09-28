import acolite as ac
import os
import pandas as pd
import numpy as np

def gee_nc2csv(input, output, longitude, latitude, lake, sta):

    folders = os.listdir(input)
    files_all = []

    for i in folders:
        if 'L2W' in i:
            dir = "{}/{}".format(input, i)
            files_all.append(dir)

    data = pd.DataFrame()
    for index in files_all:
        temp = ac.shared.nc_extract_point(index, longitude, latitude)["data"]
        date = ac.shared.nc_extract_point(index, longitude, latitude)["gatts"]["DATE_ACQUIRED"]
        CLOUD_COVER = ac.shared.nc_extract_point(index, longitude, latitude)["gatts"]["CLOUD_COVER"]
        WRS_PATH = ac.shared.nc_extract_point(index, longitude, latitude)["gatts"]["WRS_PATH"]
        WRS_ROW = ac.shared.nc_extract_point(index, longitude, latitude)["gatts"]["WRS_ROW"]

        temp["DATE_ACQUIRED"] = date
        temp["CLOUD_COVER"] = CLOUD_COVER
        temp["WRS_PATH"] = WRS_PATH
        temp["WRS_ROW"] = WRS_ROW
        temp["lake"] = lake
        temp["sta"] = sta

        if ~np.isnan(temp["Rrs_443"]):
            data = data.append(temp, ignore_index=True)

    data.to_csv(output, encoding='utf-8', index=False, header=True)



