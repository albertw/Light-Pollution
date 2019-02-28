import filecmp
import unittest
import observations as obs
import os


class HeaderTests(unittest.TestCase):

    def test_appendheader(self):
        header = obs.Header()
        line="# Comment: \n"
        header.append(line)
        self.assertEqual(header.getlines(),[line])

    def test_add_comment(self):
        header = obs.Header()
        line="# Comment: "
        header.append(line + "\n")
        comment = "LIGHTS!!!!"
        header.add_comment(comment)
        self.assertEqual(header.getlines(),[line + comment + "\n"])

class DafafileTests(unittest.TestCase):

    def test_readwrite(self):
        SQM = obs.Datafile()
        path = os.path.dirname(__file__)
        SQM.read(os.path.join(path, "ref.dat"))
        SQM.compute()
        SQM.write(os.path.join(path, "result.dat"))
        self.assertTrue(filecmp.cmp(os.path.join(path, "ref.dat"),
                                    os.path.join(path, "result.dat")), 'Files differ')

    def test_writesunmoon(self):
        SQM = obs.Datafile()
        path = os.path.dirname(__file__)
        SQM.read(os.path.join(path, "ref.dat"))
        SQM.compute()
        SQM.reduce_dark(sunlow=-18, moonlow=-7)
        SQM.write(os.path.join(path, "sunmoon.dat"))
        self.assertTrue(filecmp.cmp(os.path.join(path, "sunmoon.dat"),
                                    os.path.join(path, "sunmoonref.dat")), 'Files differ')

    def test_midnight(self):
        SQM = obs.Datafile()
        path = os.path.dirname(__file__)
        SQM.read(os.path.join(path, "ref.dat"))
        SQM.compute()
        SQM.reduce_midnight()
        SQM.write(os.path.join(path, "midnight.dat"))
        self.assertTrue(filecmp.cmp(os.path.join(path, "midnight.dat"),
                                    os.path.join(path, "midnightref.dat")), 'Files differ')


    def test_debugcsv(self):
        SQM = obs.Datafile()
        path = os.path.dirname(__file__)
        SQM.read(os.path.join(path, "ref.dat"))
        SQM.compute()
        SQM.reduce_midnight()
        SQM.debug_csv(os.path.join(path, "debugcsv.dat"))
        self.assertTrue(filecmp.cmp(os.path.join(path, "debugcsv.dat"),
                                    os.path.join(path, "debugcsvref.dat")), 'Files differ')

if __name__ == '__main__':
    unittest.main()