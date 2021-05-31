import copy
import math
import os
import random
from typing import Dict, List

from src.Chromosome import Chromosome
from src.NetworkModel import NetworkModel
from src.NetworkVisualizer import NetworkVisualizer


class GeneticAlgorithm:
    def __init__(self, network: NetworkModel, n: int, epochs: int, mutationFactor: int, singleMode: bool,
                 xoverChance: float, selection: str, succession: str, modularity: int, xoverMode: str):
        self.network = network
        self.n = n
        self.epochs = epochs
        self.mutationFactor = mutationFactor
        self.singleMode = singleMode
        self.xoverChance = xoverChance
        self.xoverMode = xoverMode
        self.selection = selection
        self.succession = succession
        self.modularity = modularity

        # Used for tracing algorithm progress
        self.costHistory: List[float] = []
        self.changesHistory: List[int] = []
        self.lastSamePos = 0
        self.lastSameVal = 0.0

        # Create initial population
        self.population = [Chromosome(network, singleMode, k=modularity) for _ in range(self.n)]

    def run(self, quiet: bool) -> float:
        for i in range(self.epochs):
            if not quiet:
                print(f'[i] Running epoch {i}')

            # Select new population
            row: List[Chromosome] = sorted(self.population, key=lambda x: x.objFunc())
            self.costHistory.append(row[0].objFunc())

            # Best one continues unmodified
            bestChrom = copy.deepcopy(row[0])

            xoverMask = []
            xovers = 0
            for _ in range(self.n - 1):
                if random.uniform(0, 1) > self.xoverChance:
                    xoverMask.append(0)
                else:
                    xoverMask.append(1)
                    xovers += 1
            onlyMutate = self.n - 1 - xovers

            samples = onlyMutate + xovers * 2
            if self.selection == 'rand':
                chosenOnes = random.choices(row, k=samples)
            elif self.selection == 'exp':
                weights = [math.exp(-x) for x in range(self.n)]
                chosenOnes = random.choices(row, weights, k=samples)
            else:
                raise ValueError('Selection must be one of the following: rand, exp')

            children: List[Chromosome] = []

            # Crossover
            idx = 0
            for bit in xoverMask:
                if bit == 0:
                    children.append(chosenOnes[idx])
                    idx += 1
                    continue

                child = Chromosome.reproduce(chosenOnes[idx], chosenOnes[idx + 1], self.xoverMode)
                children.append(child)
                idx += 2

            # Mutation
            for child in children:
                child.mutate(self.mutationFactor)

            # Succession
            if self.succession == 'best':
                combined: list[Chromosome] = row[1:] + children
                combined = sorted(combined, key=lambda x: x.objFunc())

                self.population = [bestChrom] + combined[:self.n - 1]
            elif self.succession == 'tourney':
                self.population = [bestChrom]

                for idx in range(self.n - 1):
                    if row[idx + 1].objFunc() <= children[idx].objFunc():
                        self.population.append(row[idx + 1])
                    else:
                        self.population.append(children[idx])
            else:
                raise ValueError('Invalid succession mode, expected: best or tourney')

            assert (len(self.population) == self.n)

            # Check how we're doing
            same = self.lenOfSame(i, self.costHistory[-1])
            self.changesHistory.append(same)

        # Sort final population
        self.population = sorted(self.population, key=lambda x: x.objFunc())
        return self.population[0].objFunc()

    def lenOfSame(self, epoch: int, score: float) -> int:
        """
        Returns number of epochs that resulted in the same score
        """
        if self.lastSameVal != score:
            self.lastSameVal = score
            self.lastSamePos = epoch
        return epoch - self.lastSamePos

    def result(self, visualizer: NetworkVisualizer) -> None:
        """
        Output a lot of useful information to .csv files
        Also, take care of drawing mathplotlib graphs
        :param visualizer: reference to NetworkVisualizer class
        :return: None
        """
        visualizer.drawNetworkModel(self.network, self.population[0])
        visualizer.drawObjFuncGraph(self.costHistory)
        visualizer.drawChangesHistory(self.changesHistory)

        visualizer.outputCSV('cost_history.csv',
                             ['Epoch', 'Value'],
                             [[i, val] for i, val in enumerate(self.costHistory)]
                             )

        bestResult = self.population[0]
        linksNames = [link for link in self.network.links]
        modules = bestResult.modulesPerLink()
        visualizer.outputCSV('modules_per_link.csv',
                             ['Link name', 'Modules installed'],
                             [[name, modules[name]] for name in linksNames]
                             )

        demandsNames = [demand for demand in self.network.demands]
        visualizer.outputCSV('path_choices.csv',
                             ['Demand name'] + [f'Path_{i}' for i in range(10)],
                             [
                                 [name] +
                                 [str(ch) for ch in bestResult.genes[name].path_choices]
                                 for name in demandsNames
                             ])

        perLinkDemand = bestResult.modulesPerLink()
        visualizer.outputCSV('modules_per_link_per_demand.csv',
                             ['Demand name'] + [name for name in linksNames],
                             [
                                 [name] +
                                 [str(perLinkDemand[linkName]) for linkName in linksNames]
                                 for name in demandsNames
                             ])

        demandsDiff = bestResult.calcDemands()
        visualizer.outputCSV('demand_diff_per_link.csv',
                             ['Link name', 'Demand diff'],
                             [[name, demandsDiff[name]] for name in linksNames]
                             )

        if self.singleMode:
            paths: Dict[str, List[str]] = {}
            for name in demandsNames:
                pathNo = bestResult.genes[name].path_choices.index(1)
                paths[name] = [link.name for link in self.network.getDemand(name).paths[pathNo]]

            visualizer.outputCSV('links_per_demand.csv',
                                 ['Demand name'] + [f'Link_{i}' for i in range(8)],
                                 [[name] + paths[name] for name in demandsNames]
                                 )
        else:
            visualizer.outputCSV('link_per_demand.csv',
                                 ['Demand name', '0'], [['Not applicable...', '0']])

        bestResult.saveToXML(os.path.join(visualizer.outputDir, 'solution.xml'))

        visualizer.outputCSV('summary.csv',
                             ['Parameter', 'Value'],
                             [
                                 ['Epochs count', self.epochs],
                                 ['Population size', self.n],
                                 ['Mutation factor', self.mutationFactor],
                                 ['Single mode', self.singleMode],
                                 ['Modularity factor', self.modularity],
                                 ['Network size (nodes)', len(self.network.nodes)],
                                 ['Network size (links)', len(self.network.links)],
                                 ['Network size (demands)', len(self.network.demands)],
                                 ['Best score', bestResult.objFunc()],
                                 ['Total modules used', sum(bestResult.modulesPerLink().values())]
                             ]
                             )
