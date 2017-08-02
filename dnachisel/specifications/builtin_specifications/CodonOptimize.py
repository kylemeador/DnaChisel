import numpy as np

from ..Specification import CodonSpecification
from ..SpecEvaluation import SpecEvaluation
from dnachisel.biotools import (CODON_USAGE_TABLES, CODONS_TRANSLATIONS,
                                group_nearby_indices)
from dnachisel.Location import Location

class CodonOptimize(CodonSpecification):
    """Specification to codon-optimize a coding sequence for a particular species.

    Several codon-optimization policies exist. At the moment this Specification
    implements a method in which codons are replaced by the most frequent
    codon in the species.

    (as long as this doesn't break any Specification or lowers the global
    optimization objective)

    Supported speciess are ``E. coli``, ``S. cerevisiae``, ``H. Sapiens``,
    ``C. elegans``, ``D. melanogaster``, ``B. subtilis``.

    Parameters
    ----------

    species
      Name of the species to codon-optimize for. Supported speciess are
      ``E. coli``, ``S. cerevisiae``, ``H. Sapiens``, ``C. elegans``,
      ``D. melanogaster``, ``B. subtilis``.
      Note that the species can be omited if a ``codon_usage_table`` is
      provided instead

    location
      Pair (start, end) indicating the position of the gene to codon-optimize.
      If not provided, the whole sequence is considered as the gene. Make
      sure the length of the sequence in the location is a multiple of 3.
      The location strand is either 1 if the gene is encoded on the (+) strand,
      or -1 for antisense.

    codon_usage_table
      A dict of the form ``{"TAC": 0.112, "CCT": 0.68}`` giving the RSCU table
      (relative usage of each codon). Only provide if no ``species`` name
      was provided.

    Examples
    --------

    >>> objective = CodonOptimizationSpecification(
    >>>     species = "E. coli",
    >>>     location = (150, 300), # coordinates of a gene
    >>>     strand = -1
    >>> )


    """

    best_possible_score = 0

    def __init__(self, species=None, location=None,
                 codon_usage_table=None, boost=1.0):
        self.boost = boost
        self.location = location
        self.species = species
        if species is not None:
            codon_usage_table = CODON_USAGE_TABLES[self.species]
        if codon_usage_table is None:
            raise ValueError("Provide either an species name or a codon "
                             "usage table")
        self.codon_usage_table = codon_usage_table

    def evaluate(self, problem):
        """ Return the sum of all codons frequencies.

        Note: no smart localization currently, the sequence is improved via

        """
        location = (self.location if self.location is not None
                    else Location(0, len(problem.sequence)))
        subsequence = location.extract_sequence(problem.sequence)
        length = len(subsequence)
        if (length % 3):
            raise ValueError(
                "CodonOptimizationSpecification on a window/sequence"
                "with size %d not multiple of 3)" % length
            )
        codons = [
            subsequence[3 * i:3 * (i + 1)]
            for i in range(int(length / 3))
        ]
        # the are arrays:
        current_usage, optimal_usage = [np.array(e) for e in zip(*[
            (self.codon_usage_table[codon],
             self.codon_usage_table[CODONS_TRANSLATIONS[codon]])
            for codon in codons
        ])]
        non_optimality = optimal_usage - current_usage
        nonoptimal_indices = 3*np.nonzero(non_optimality)
        if self.location.strand == -1:
            nonoptimal_indices = self.location.end - nonoptimal_indices
        else:
            nonoptimal_indices += self.location.start
        locations = [
            Location(group[0], group[-1], )
            for group in group_nearby_indices(nonoptimal_indices,
                                              max_group_spread=20)
        ]
        score = -non_optimality.sum()
        return SpecEvaluation(
            self, problem, score=score, locations=locations,
            message="Codon opt. on window %s scored %.02E" %
                    (location, score)
        )

    def localized_on_window(self, new_location, start_codon, end_codon):
        """Relocate without changing much."""
        return self.__class__(species=self.species, location=new_location,
                              boost=self.boost)


    def __str__(self):
        """Represent."""
        return "CodonOptimize(%s, %s)" % (str(self.location), self.species)

    def __repr__(self):
        """Represent."""
        return "CodonOptimize(%s, %s)" % (str(self.location), self.species)
