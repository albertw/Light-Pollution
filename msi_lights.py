#!/usr/bin/env python
""""
Given a csv file of locations of interest and a csv file of locations of lights,
we compute the weighted melatonin supression effect of lights within a given radius,
and return the list of those lights.
"""
import argparse

import numpy as np
import pandas as pd

pd.set_option('display.float_format', lambda x: '%.6f' % x)


def lights(csv):
    """ Read in a csv file of lights and return a dataframe.
        Assumes csv file is in the format of the Cork County Council data
    """
    df = pd.read_csv(csv, low_memory=False)
    df.rename(columns={'12) Easting_ITM': 'easting',
                       '13) Northing_ITM': 'northing',
                       '39) Lamp Type': 'lamp_type',
                       '40) Wattage': 'wattage',
                       'Easting_ITM': 'easting',
                       'Northing_ITM': 'northing',
                       'Lamp Type': 'lamp_type',
                       'Wattage': 'wattage'
                       },
              inplace=True)
    lampdf = pd.merge(df, msi_types(), on=['lamp_type'], how='left')
    lampdf['Lamp_Lumens'] = lampdf['wattage'] * lampdf['lumens/W']
    return lampdf


def msi_types():
    """ Melatonin Suppression Index for light types used for weighting
        c.f. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3702543/
    """
    typedict = {'lamp_type': {0: 'SOX',
                              1: 'SON',
                              2: 'Fluorescent',
                              3: 'MHL',
                              4: 'LED 4000K',
                              5: 'Tungsten',
                              6: 'Halogen',
                              7: 'Mercury',
                              8: 'CFL'},
                'MSI': {0: 0.017,
                        1: 0.11800000000000001,
                        2: 0.435,
                        3: 0.624,
                        4: 0.452,
                        5: 0.255,
                        6: 0.377,
                        7: 0.435,
                        8: 0.435},
                'lumens/W': {0: 170.0,
                             1: 120.0,
                             2: 90.0,
                             3: 120.0,
                             4: 75.0,
                             5: 15.0,
                             6: 24.0,
                             7: 10.5,
                             8: 60.0}}
    return pd.DataFrame(typedict)


def read_locations(csv):
    """ Read the locations to study.
        This assumes the data is in the format of the sample Cork locations
        with eircode and IRENET95 easting and northing.
    """
    _df = pd.read_csv(csv)
    _df.rename(columns={'Unnamed: 1': 'eircode',
                        'Eircode': 'eircode',
                        'IRENET95-East': 'easting',
                        'IRENET95-North': 'northing'},
               inplace=True)
    return _df


def nearby_lamps(dataframe, east, north, contribution=0, radius=150, quick=False):
    """ Return the df of lamps near (within 1000m of) the given easting & northing
        if quick is true we just get the lamps in a square centered on the east,north
        if False we compute the euclidian distance.
    """
    # quick square centered on the location
    df = (dataframe.loc[(abs(dataframe['easting'] - east) < radius) &
                        (abs(dataframe['northing'] - north) < radius)]).copy()

    if not quick:
        # euclidian circle around the location
        point = [east, north]
        # subtract the point from each df[easting,northing], square the results, add them and sqrt them
        df['distance'] = df[['easting', 'northing']].sub(np.array(point)).pow(2).sum(1).pow(0.5)
        df = df.loc[df['distance'] < radius]

    # Calculate the lumens at the house
    df['House_Lumens'] = df["wattage"] / (df["distance"] * df["distance"])

    # Calculate the weighted MSI contribution and sort by that
    df['MSI_weighted'] = df['House_Lumens'] * df['MSI']
    df.sort_values('MSI_weighted', ascending=False, inplace=True)

    # Discard lights that result in a small correction to the previous total
    df['expanded'] = df['MSI_weighted'].expanding().sum()
    df['contrib'] = df['MSI_weighted'] / df['expanded']
    try:
        df.contrib.iloc[0] = 1
    except IndexError:
        # Probably empty df
        pass
    return df.loc[df['contrib'] > contribution]


def convert_to_latlon(row):
    """ Convert from easting and northing to lat/lon WSG84
    """
    x, y = transformer.transform(row['easting'], row['northing'])
    return pd.Series({'lat': y, 'lon': x})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Location and streetlight MSI processing.')

    parser.add_argument('-i',
                        required=True,
                        help="Input streetlamp file. Assumed to be in the same structure as 'CorkCo.csv'",
                        dest='lightfile')
    parser.add_argument('-l',
                        required=True,
                        help="Input location file. Assumed to be in the same structure as 'House_coords_BE'",
                        dest='locationfile')
    # parser.add_argument('-m', '--mapfile', dest='mapfile', default='mapfile',
    #                    help='Bese filename to write maps to. (Default: %(default)s).')
    parser.add_argument('-r', '--radius', dest='radius', default=150,
                        help='Radius from location to look for lights. (Default: %(default)s).')

    args = parser.parse_args()

    # if args.mapfile:
    #    from pyproj import Transformer
    #    import mplleaflet
    #    transformer = Transformer.from_proj(2157, 4326)

    lightsdf = lights(args.lightfile)

    locations = read_locations(args.locationfile)
    for location in locations.iterrows():
        # TODO This will be very slow if we have lots of locations, but good enough for now.
        print("Location: " + location[1].eircode)
        lamps = nearby_lamps(lightsdf, location[1].easting, location[1].northing, radius=int(args.radius))
        print("Lamps: " + str(len(lamps)))
        if not lamps.empty:
            print(lamps.to_csv())
        print()
