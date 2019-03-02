import copy
import datetime
import math
import tempfile

import ephem
import pandas as pd


class Header:
    """ The format is described at
    https://www.darksky.org/wp-content/uploads/bsk-pdf-manager/47_SKYGLOW_DEFINITIONS.PDF
    We'll assume we get a valid file to start and for now we'll just try to add
    comments.
    """

    def __init__(self):
        """ Just a list of strings for now"""
        self.lines = []

    def append(self, line):
        """ Add a new line to the header"""
        self.lines.append(line)

    def add_comment(self, comment):
        """ Find a free comment line and add in the new comment"""
        try:
            free = [i for i, s in enumerate(self.lines) if s == "# Comment: \n"][0]
            self.lines[free] = "# Comment: " + comment + "\n"
        except IndexError as e:
            print("No free comment lines..." + str(e))
            raise

    def getlines(self):
        return self.lines


class Datafile:
    """ Class to handle a datafile"""

    def __init__(self):
        """ Initialise with the filename"""
        self.datafile = ""
        self.sunlow = 0
        self.moonlow = 0
        self.header = Header()
        self.location = ephem.Observer()
        self.df = pd.DataFrame()
        self.sunmoon = pd.DataFrame()
        self.midnight = pd.DataFrame()

    def read(self, datafile):
        """ read in the datafile"""
        self.datafile = datafile
        self.df = pd.read_csv(self.datafile, comment='#', sep=";",
                              names=["UTCDate", "LocalDate", "Temp", "Volts", "MSAS"],
                              header=None,
                              parse_dates=["UTCDate", "LocalDate"])
        self.df = self.df.round({'MSAS': 2})

        with open(self.datafile) as f:
            for line in f:
                if "Position" in line:
                    [lat, lon, ele] = line.split(":")[1].split(",")
                    self.location.lon = lon
                    self.location.lat = lat
                    self.location.elevation = int(ele)
                if "#" not in line:
                    break
                self.header.append(line)

        return self.df

    def _sunalt(self, x):
        """ Compute the altitude of the sun in degrees."""
        loc = self.location
        loc.date = x['UTCDate']
        sun = ephem.Sun()
        sun.compute(loc)
        return math.degrees(sun.alt)

    def _moonalt(self, x):
        """ Compute the altitude of the moon in degrees."""
        loc = self.location
        loc.date = x['UTCDate']
        moon = ephem.Moon()
        moon.compute(loc)
        return math.degrees(moon.alt)

    def _nightssolarantitransit(self, x):
        """ Compute the local solar antitransit time
            - when the sun is at it's lowest, solar midnight

            We set the UTCdate of the location back 12 hours and
            calculate the next_antitransit(Sun) to get that nights time.
            """
        loc = self.location
        loc.date = x['UTCDate'] - datetime.timedelta(hours=12)
        return loc.next_antitransit(ephem.Sun()).datetime().strftime('%Y-%m-%d %H:%M:%S')

    def compute(self):
        """ Compute:
            - the altitude of the sun and moon and add these as columns.
            - the original date strings
        """

        # Add new columns for the sun and moon altitude
        self.df['sunalt'] = self.df.apply(self._sunalt, 1)
        self.df['moonalt'] = self.df.apply(self._moonalt, 1)

        # Write columns with the datetime string format the file needs to be in
        self.df['OrigUTCDate'] = self.df['UTCDate'].apply(lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.000'))
        self.df['OrigLocalDate'] = self.df['LocalDate'].apply(lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.000'))

        # Calculate local solar midnight and make it a datetime object
        self.df['NightsSolarAntiTransit'] = self.df.apply(self._nightssolarantitransit, 1)
        self.df['NightsSolarAntiTransit'] = pd.to_datetime(self.df['NightsSolarAntiTransit'])

        return self.df

    def reduce_dark(self, sunlow=-18, moonlow=-10):
        """ Remove the rows from the df where the sun and
            moon are below given altitudes
            Defaults from : https://academic.oup.com/mnras/article/412/1/33/984247
        """
        df = self.df
        self.sunmoon = df.loc[(df['sunalt'] < sunlow) & (df['moonalt'] < moonlow)]
        if self.sunmoon.empty:
            raise ValueError('Now rows meet the Sun and Moon altitude criteria.')
        else:
            return self.sunmoon

    def reduce_midnight(self):
        """ Select only rows that are between one hour either side of 'antitransit' midnight
            AND where the Sun and Moon altitude criteria are met."""

        if self.sunmoon.empty:
            self.reduce_dark()
        df = self.sunmoon

        self.midnight = df.loc[((df['UTCDate'] - df['NightsSolarAntiTransit']) < datetime.timedelta(hours=1)) &
                               ((df['NightsSolarAntiTransit'] - df['UTCDate']) < datetime.timedelta(hours=1))]
        return self.midnight

    def write(self, fname=None):
        """ Write out the new observation file.
            If self.midnight we write it.
            else if self.sunmoon exists we write it
            else we just write the original df
            """
        header = copy.deepcopy(self.header)
        if not self.midnight.empty:
            df = self.midnight.copy()
            header.add_comment("Data where the sun and moon are low and 1 hour either side of solar antitransit.")
            header.add_comment("5% Percentile = " + str(df.MSAS.quantile(q=.05)) +
                               "; 95% Percentile = " + str(df.MSAS.quantile(q=.95)))
            header.add_comment("Local solarantitransit 'midnight' ranges from " +
                               str(min(df['NightsSolarAntiTransit'].dt.time)) + " to " +
                               str(max(df['NightsSolarAntiTransit'].dt.time)))
        elif not self.sunmoon.empty:
            df = self.sunmoon.copy()
            header.add_comment("Data where the sun and moon are low.")
            header.add_comment("5% Percentile = " + str(df.MSAS.quantile(q=.05)) +
                               "; 95% Percentile = " + str(df.MSAS.quantile(q=.95)))
        else:
            df = self.df.copy()

        if not fname:
            file = tempfile.NamedTemporaryFile(mode="w+")
        else:
            file = open(fname, "w", newline='\r\n')

        for line in header.getlines():
            file.write(line)

        # Temp is to one decimal place but the other values are to two
        df['Temp'] = df['Temp'].map(lambda x: '{0:.1f}'.format(x))
        df[['OrigUTCDate', 'OrigLocalDate', 'Temp', 'Volts', 'MSAS']].to_csv(file,
                                                                             mode='a',
                                                                             header=False,
                                                                             index=False,
                                                                             sep=";",
                                                                             float_format='%.2f')
        if not fname:
            file.seek(0)
            print(file.read())
        file.close()

    def debug_csv(self, fname):
        """ Write out the full df for analysis"""

        df = self.df.copy()

        file = open(fname, "w", newline='\r\n')

        # Temp is to one decimal place but the other values are to two
        df['Temp'] = df['Temp'].map(lambda x: '{0:.1f}'.format(x))
        df.to_csv(file,
                  mode='a',
                  header=True,
                  index=False,
                  sep=";", float_format='%.2f')
        file.close()
