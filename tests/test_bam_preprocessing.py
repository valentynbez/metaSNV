import unittest

from metaSNV.bam_preprocessing import BAMInfo, BAMReference

class TestBAMReference(unittest.TestCase):
    def setUp(self) -> None:
        self.test_ref = BAMReference('sample', 'ref', 4)
        for (x, y) in [(1, 10), (2, 12), (3, 14), (4, 14)]:
            self.test_ref.add_coverage(x, y)

    def test_positions(self):
        self.assertEqual(self.test_ref.positions(), [1, 2, 3, 4])

    def test_coverage(self):
        self.assertEqual(self.test_ref.coverage_depth('mean'), 12.5)
        self.assertEqual(self.test_ref.coverage_depth('median'), 13)
        self.assertEqual(self.test_ref.coverage_depth('raw'), [10, 12, 14, 14])
        with self.assertRaises(ValueError):
            self.test_ref.coverage_depth('invalid')

    def test_breadth(self):
        self.assertEqual(self.test_ref.coverage_breadth(depth=1), 1)
        self.assertEqual(self.test_ref.coverage_breadth(depth=12), 0.75)
        self.assertEqual(self.test_ref.coverage_breadth(depth=14), 0.5)


class TestBAMInfo(unittest.TestCase):
    def setUp(self) -> None:
        self.test_bam = BAMInfo.from_bam('tests/data/test.bam')
        self.references = ['refGenome1clus', 'refGenome2clus', 'refGenome3clus']

    def test_references(self):
        self.assertEqual(self.test_bam.sample, 'test')

    def test_reference_names(self):
        self.assertEqual(self.test_bam.get_reference_names(),
                         self.references)

    def test_get_reference(self):
        self.assertEqual(self.test_bam['refGenome1clus'].ref_name,
                         self.references[0])

    def test_coverage(self):
        ref = self.test_bam['refGenome1clus']
        self.assertEqual(ref.coverage_depth('median'), 16)
        self.assertEqual(ref.coverage_breadth(1), 0.99938)

