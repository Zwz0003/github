import acolite as ac
import os
import datetime
import pandas as pd
import shutil

def acolite_gee_run(input,  #input path
                    output_nc, #output path
                    output_csv,
                    sources, #['Landsat 5', 'Landsat 7','Landsat 8','Landsat 9', 'Sentinel-2']
                    point_list_dir,
                    sdate,
                    edate,
                    time_start = 0):

    # save data as nc
    point_list = pd.read_csv(point_list_dir)
    for index, point in point_list.iterrows():
        longitude = point["lon"]
        latitude = point["lat"]

        ac.gem.extract(st_lon=longitude, st_lat=latitude, sdate=sdate, edate=edate,
                             output= input, sources=sources)
        time_start = datetime.datetime.now()
        time_start = time_start.strftime('%Y%m%d_%H%M%S')
        settings = {'inputfile': input, 'output': output_nc, 'polygon': '', 'l2w_parameters': ['Rrs_*'], 'rgb_rhot': False, 'rgb_rhos': False, 'map_l2w': False, 'runid': time_start}

        l1r_setu = ac.acolite.settings.parse("L8_OLI", settings = settings)

        l1r_files = []
        delete = []
        for i in os.listdir(input):
            temp = "{}/{}".format(input, i)
            delete.append(temp)
            files = os.listdir(temp)
            for j in files:
                dir = "{}/{}/{}".format(settings["inputfile"], i, j)
                l1r_files.append(dir)

        ## do atmospheric correction
        l2r_files, l2t_files = [], []
        l2w_files = []
        for l1r in l1r_files:

            gatts = ac.shared.nc_gatts(l1r)

            if 'acolite_file_type' not in gatts: gatts['acolite_file_type'] = 'L1R'
            ## do VIS-SWIR atmospheric correction
            if l1r_setu['atmospheric_correction']:
                if gatts['acolite_file_type'] == 'L1R':
                    ## run ACOLITE
                    ret = ac.acolite.acolite_l2r(l1r, settings=l1r_setu, verbosity=ac.config['verbosity'])
                    if len(ret) != 2: continue
                    l2r, l2r_setu = ret
                else:
                    l2r = '{}'.format(l1r)
                    l2r_setu = ac.acolite.settings.parse(gatts['sensor'], settings=l1r_setu)

                if (l2r_setu['adjacency_correction']):
                    ret = None
                    ## acstar3 adjacency correction
                    if (l2r_setu['adjacency_method'] == 'acstar3'):
                        ret = ac.adjacency.acstar3.acstar3(l2r, setu=l2r_setu, verbosity=ac.config['verbosity'])
                    ## GLAD
                    if (l2r_setu['adjacency_method'] == 'glad'):
                        ret = ac.adjacency.glad.glad_l2r(l2r, verbosity=ac.config['verbosity'], settings=l2r_setu)
                    l2r = [] if ret is None else ret

                ## if we have multiple l2r files
                if type(l2r) is not list: l2r = [l2r]
                l2r_files += l2r

                if l2r_setu['l2r_export_geotiff']:
                    for ncf in l2r:
                        ac.output.nc_to_geotiff(ncf, match_file=l2r_setu['export_geotiff_match_file'],
                                                cloud_optimized_geotiff=l1r_setu['export_cloud_optimized_geotiff'],
                                                skip_geo=l2r_setu['export_geotiff_coordinates'] is False)

                        if l2r_setu['l2r_export_geotiff_rgb']: ac.output.nc_to_geotiff_rgb(ncf, settings=l2r_setu)

                ## make rgb rhos maps
                if l2r_setu['rgb_rhos']:
                    l2r_setu_ = {k: l1r_setu[k] for k in l2r_setu}
                    l2r_setu_['rgb_rhot'] = False
                    for ncf in l2r:
                        ac.acolite.acolite_map(ncf, settings=l2r_setu_, plot_all=False)

                ## compute l2w parameters
                if l2r_setu['l2w_parameters'] is not None:
                    if type(l2r_setu['l2w_parameters']) is not list: l2r_setu['l2w_parameters'] = [l2r_setu['l2w_parameters']]
                    for ncf in l2r:
                        ret = ac.acolite.acolite_l2w(ncf, settings=l2r_setu)
                        if ret is not None:
                            if l2r_setu['l2w_export_geotiff']: ac.output.nc_to_geotiff(ret, match_file=l2r_setu[
                                'export_geotiff_match_file'],
                                                                                       cloud_optimized_geotiff=l1r_setu[
                                                                                           'export_cloud_optimized_geotiff'],
                                                                                       skip_geo=l2r_setu[
                                                                                                    'export_geotiff_coordinates'] is False)
                            l2w_files.append(ret)

                            ## make l2w maps
                            if l2r_setu['map_l2w']:
                                ac.acolite.acolite_map(ret, settings=l2r_setu)
                            ## make l2w rgb
                            if l2r_setu['rgb_rhow']:
                                l2r_setu_ = {k: l1r_setu[k] for k in l2r_setu}
                                l2r_setu_['rgb_rhot'] = False
                                l2r_setu_['rgb_rhos'] = False
                                ac.acolite.acolite_map(ret, settings=l2r_setu_, plot_all=False)
        #   end save
        name_output = "{}/{}.csv".format(output_csv, index)
        ac.gee_nc2csv.gee_nc2csv(input= output_nc, output = name_output, longitude = longitude, latitude = latitude, lake = point["lake"], sta = point["sta"])
        
        for file_nc in os.listdir(output_nc):
            temp = "{}/{}".format(output_nc, file_nc)
            os.remove(temp)
        for file in delete:
            shutil.rmtree(file)







