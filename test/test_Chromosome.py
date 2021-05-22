import random
from unittest import TestCase

from src.Chromosome import Chromosome
from src.NetworkModel import NetworkModel, Link, Demand, Node


class TestChromosome(TestCase):
    def setUp(self):
        random.seed(1024)
        self.assertEqual(random.randint(0, 1000), 816)

        self.network = NetworkModel('./testModel.txt')
        self.network.parse()


class TestReproductionSingleMode(TestChromosome):
    def setUp(self):
        super().setUp()
        self.chromosome1 = Chromosome(self.network)
        self.chromosome2 = Chromosome(self.network)

        self.child1, self.child2 = Chromosome.reproduce(self.chromosome1, self.chromosome2)

    def test_chromosome_configs(self):
        # Check that single_mode was preserved
        self.assertEqual(self.child1.singleMode, self.chromosome1.singleMode)
        self.assertEqual(self.child2.singleMode, self.chromosome2.singleMode)
        for gene in self.child1.genes.values():
            self.assertEqual(gene.singleMode, self.child1.singleMode)
        for gene in self.child2.genes.values():
            self.assertEqual(gene.singleMode, self.child2.singleMode)

    def test_genes_count(self):
        self.assertEqual(len(self.child1.genes), len(self.chromosome1.genes))
        self.assertEqual(len(self.child2.genes), len(self.chromosome2.genes))

        for gene in self.child1.genes.values():
            self.assertEqual(len(gene.modules), len(self.network.links))
            self.assertEqual(
                len(gene.path_choices),
                self.network.getDemand(gene.name).pathsCount()
            )
        for gene in self.child2.genes.values():
            self.assertEqual(len(gene.modules), len(self.network.links))
            self.assertEqual(
                len(gene.path_choices),
                self.network.getDemand(gene.name).pathsCount()
            )


class TestObjFunc(TestChromosome):
    def setUp(self):
        super().setUp()
        self.chromosome = Chromosome(self.network, singleMode=True)

    def test_modules_count_ceil(self):
        self.assertDictEqual(
            self.chromosome.modulesPerLink(),
            {'Link_0_1': 0.0, 'Link_0_2': 2.0,
             'Link_2_3': 2.0, 'Link_3_1': 1.0}
        )

    def test_modules_count_without_ceil(self):
        self.assertDictEqual(
            self.chromosome.modulesPerLink(ceil=False),
            {
                'Link_0_1': 0.0,
                'Link_0_2': 1.5710835338674305,
                'Link_2_3': 1.3138313299610425,
                'Link_3_1': 0.445120740777845
            }
        )

    def test_fixed_modules_count(self):
        self.assertDictEqual(
            self.chromosome.fixedModulesPerLink(),
            {
                'Link_0_1': 0.0, 'Link_0_2': 2.0,
                'Link_2_3': 2.0, 'Link_3_1': 1.0
            }
        )

    def test_obj_demands_diff_ceil(self):
        self.assertDictEqual(
            self.chromosome.calcDemands(ceil=True),
            {
                'Link_0_1': 0.0,
                'Link_0_2': 717,
                'Link_2_3': 891,
                'Link_3_1': 427
            }
        )

    def test_obj_demands_diff_without_ceil(self):
        self.assertDictEqual(
            self.chromosome.calcDemands(ceil=False),
            {
                'Link_0_1': 0.0,
                'Link_0_2': 450.21395806554176,
                'Link_2_3': 464.2030872357684,
                'Link_3_1': 81.86510076381961
            }
        )

    def test_obj_func_value(self):
        self.assertEqual(
            self.chromosome.objFunc(),
            59.9628214606513
        )

