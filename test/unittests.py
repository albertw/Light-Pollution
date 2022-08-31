import os
import unittest

import observations as obs


class HeaderTests(unittest.TestCase):

    def test_appendheader(self):
        header = obs.Header()
        line = "# Comment: \n"
        header.append(line)
        self.assertEqual(header.getlines(), [line])

    def test_add_comment(self):
        header = obs.Header()
        line = "# Comment: "
        header.append(line + "\n")
        comment = "LIGHTS!!!!"
        header.add_comment(comment)
        self.assertEqual(header.getlines(), [line + comment + "\n"])


class DafafileTests(unittest.TestCase):

    def test_readwrite(self):
        SQM = obs.Datafile()
        path = os.path.dirname(__file__)
        SQM.read(os.path.join(path, "ref.dat"))
        SQM.compute()
        SQM.write(os.path.join(path, "result.dat"))
        self.assertEqual(filecmp(os.path.join(path, "ref.dat"),
                                    os.path.join(path, "result.dat")), set(), 'Files differ')

    def test_writesunmoon(self):
        SQM = obs.Datafile()
        path = os.path.dirname(__file__)
        SQM.read(os.path.join(path, "ref.dat"))
        SQM.compute()
        SQM.reduce_dark()
        SQM.write(os.path.join(path, "sunmoon.dat"))
        self.assertEqual(filecmp(os.path.join(path, "sunmoon.dat"),
                                    os.path.join(path, "sunmoonref.dat")), set(), 'Files differ')

    def test_midnight(self):
        SQM = obs.Datafile()
        path = os.path.dirname(__file__)
        SQM.read(os.path.join(path, "ref.dat"))
        SQM.compute()
        SQM.reduce_midnight()
        SQM.write(os.path.join(path, "midnight.dat"))
        self.assertEqual(filecmp(os.path.join(path, "midnight.dat"),
                                    os.path.join(path, "midnightref.dat")), set(), 'Files differ')

    def test_debugcsv(self):
        SQM = obs.Datafile()
        path = os.path.dirname(__file__)
        SQM.read(os.path.join(path, "ref.dat"))
        SQM.compute()
        SQM.reduce_midnight()
        SQM.debug_csv(os.path.join(path, "debugcsv.dat"))
        self.assertEqual(filecmp(os.path.join(path, "debugcsv.dat"),
                                    os.path.join(path, "debugcsvref.dat")), set(), 'Files differ')

def filecmp(f1, f2):
    with open(f1, 'r') as fp:
        l1 = fp.readlines()
    with open(f2, 'r') as fp:
        l2 = fp.readlines()
    print(set(l1) - set(l2))
    return(set(l1) - set(l2))

if __name__ == '__main__':
    unittest.main()
