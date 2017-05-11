#   Copyright (c) 2016 CNRS - Centre national de la recherche scientifique.
#   All rights reserved.
#
#   Written by Telmo Menezes <telmo@telmomenezes.com>
#
#   This file is part of GraphBrain.
#
#   GraphBrain is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   GraphBrain is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with GraphBrain.  If not, see <http://www.gnu.org/licenses/>.


import math
import logging
import numpy as np
from cachetools import LRUCache
import gb.hypergraph.hypergraph as hyperg
import gb.hypergraph.symbol as sym
import gb.hypergraph.edge as ed
import gb.nlp.parser as par
import gb.knowledge.synonyms as ksyn
from gb.sense.candidate_metrics import CandidateMetrics


MAX_PROB = -7.
SIMILARITY_THRESHOLD = 0.7
MAX_COUNT = -1
STAR_LIMIT = 1000
MAX_WORDS = 50


def check_namespace(symbol, namespaces):
    symb_ns = sym.nspace(symbol)
    if namespaces:
        for ns in namespaces:
            if symb_ns.startswith(ns):
                return True
        return False
    else:
        return True


class Disambiguation(object):
    def __init__(self, hg, parser):
        self.hg = hg
        self.parser = parser
        self.cache = LRUCache(maxsize=100000000)

    def words_around_symbol(self, symbol):
        edges = self.hg.star(symbol, limit=STAR_LIMIT)
        words = set()
        for edge in edges:
            for entity in edge:
                for symbol in ed.symbols(entity):
                    term = sym.symbol2str(symbol)
                    for token in term.split():
                        word = self.parser.make_word(token)
                        if word.prob < MAX_PROB and np.count_nonzero(word.vector) > 0:
                            words.add(word)

        return words

    def words_from_text(self, text):
        words = set()

        tokens = text.replace(':', ' ').replace(';', ' ').replace(',', ' ').replace('.', ' ').replace('?', ' ')\
            .replace('!', ' ').split()

        if 0 < MAX_WORDS <= len(tokens):
            return tokens[:MAX_WORDS]

        for token in tokens:
            word = self.parser.make_word(token)
            if word.prob < MAX_PROB and np.count_nonzero(word.vector) > 0:
                words.add(word)
        return words

    def words_similarity(self, words1, words2, exclude):
        # print('sizes %s %s' % (len(words1), len(words2)))
        logging.debug('starting to compute words similarity')
        score = 0.
        count = 0
        for word1 in words1:
            for word2 in words2:
                if (word1.text not in exclude) or (word2.text not in exclude):
                    pair_id1 = '%s %s' % (word1.text, word2.text)
                    pair_id2 = '%s %s' % (word2.text, word1.text)
                    if pair_id1 in self.cache:
                        local_score = self.cache[pair_id1]
                    elif pair_id2 in self.cache:
                        local_score = self.cache[pair_id2]
                    else:
                        sim = word1.similarity(word2)
                        prob1 = math.exp(word1.prob)
                        prob2 = math.exp(word2.prob)
                        local_score = 0.
                        if sim > SIMILARITY_THRESHOLD:
                            local_score = 1. / (prob1 * prob2 * sim)
                            self.cache[pair_id1] = local_score
                    score += local_score
                    count += 1
                    if 0 < MAX_COUNT <= count:
                        logging.debug('words similarity computed [interrupted: MAX_COUNT] (count: %s)' % count)
                        return score

        logging.debug('words similarity computed (count: %s)' % count)
        return score

    def best_sense(self, roots, aux_text, namespaces=None):
        candidates = set()
        exclude = set()
        for root in roots:
            candidates = candidates.union(self.hg.symbols_with_root(root))
            text = sym.symbol2str(root)
            for token in text.split():
                exclude.add(token)
        words1 = self.words_from_text(aux_text)
        best = None
        best_cm = CandidateMetrics()
        for candidate in candidates:
            if check_namespace(candidate, namespaces):
                words2 = self.words_around_symbol(candidate)
                cm = CandidateMetrics()
                cm.score = self.words_similarity(words1, words2, exclude)
                cm.degree = ksyn.degree(self.hg, candidate)
                logging.info('%s %s' % (candidate, cm))
                if cm.better_than(best_cm):
                    best_cm = cm
                    best = candidate

        return best, best_cm


if __name__ == '__main__':
    hgr = hyperg.HyperGraph({'backend': 'leveldb',
                             'hg': 'wordnet_wikidata.hg'})
    p = par.Parser()
    d = Disambiguation(hgr, p)

    r1 = ['stocks', 'stock']
    text1 = "Chinese stocks end year with double-digit losses"

    r2 = ['cambridge']
    text2 = "Cambridge near Boston in the United States."
    text3 = "Cambridge near London in England."

    print(d.best_sense(r2, text3))
