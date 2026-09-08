import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from conversational_search.attribute_index import AttributeIndex, QueryAtom, build_attribute_index, extract_facts, query_atoms
from conversational_search.intent import IntentState, Requirement, apply_user_message


class AttributeIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.catalog = Path(self.tmp.name) / 'catalog.jsonl'
        products = [
            {'parent_asin':'a', 'details':{'Material':'100% Cotton','Color':'Blue','Size':'Medium'}},
            {'parent_asin':'b', 'title':'Cotton-free blueberry design', 'details':{}},
            {'parent_asin':'c', 'details':{}},
            {'parent_asin':'d', 'details':{'Material':['cotton','cotton-free']}},
            {'parent_asin':'e', 'details':{'Material':'20% cotton, 80% polyester','Color':'Red'}},
            {'parent_asin':'f', 'details':{'Package Dimensions':'size medium', 'Manufacturer':'Cotton Works'}},
        ]
        self.catalog.write_text(''.join(json.dumps(p)+'\n' for p in products))
        self.path = Path(self.tmp.name) / 'index.sqlite'
        build_attribute_index(self.catalog,self.path)
        self.index = AttributeIndex(self.path,self.catalog)
        self.addCleanup(self.index.close)

    def test_word_boundaries_and_negation(self):
        self.assertEqual(self.index.evidence('b',QueryAtom('material','cotton')),('counterevidence',0))
        self.assertEqual(self.index.evidence('b',QueryAtom('color','blue')),('unknown',0))
        self.assertEqual(self.index.evidence('b',QueryAtom('material','cotton',-1)),('match',0))

    def test_missing_mismatching_and_conflicting_metadata_are_not_hard_rejections(self):
        atom=QueryAtom('material','cotton')
        self.assertEqual(self.index.evidence('c',atom),('unknown',0))
        self.assertEqual(self.index.evidence('d',atom),('conflict',0))
        # A listed red parent product may have a blue variant, so absence is unknown.
        self.assertEqual(self.index.evidence('e',QueryAtom('color','blue')),('unknown',0))
        ids=('c','d','b','a'); self.assertCountEqual(self.index.rerank(ids,(atom,)),ids)

    def test_precise_composition_is_not_reduced_to_contains(self):
        state=IntentState(requirements=(Requirement('100% cotton','answer',1,'material'),))
        self.assertEqual(query_atoms(state),(QueryAtom('material','pure:cotton'),))
        self.assertEqual(self.index.evidence('a',query_atoms(state)[0]),('match',1))
        self.assertEqual(self.index.evidence('e',query_atoms(state)[0]),('unknown',0))

    def test_field_provenance_and_irrelevant_metadata(self):
        records=self.index.explain('a',QueryAtom('color','blue'))
        self.assertEqual(records[0]['source'],'details.Color')
        self.assertEqual(records[0]['raw'],'Blue')
        self.assertEqual(self.index.evidence('f',QueryAtom('size','m')),('unknown',0))
        self.assertEqual(self.index.evidence('f',QueryAtom('material','cotton')),('unknown',0))

    def test_missing_details_retains_text_evidence(self):
        facts=extract_facts({'title':'Blue cotton shirt','features':['Machine washable'],'details':None})
        self.assertTrue(any(f.attribute=='material' and f.value=='cotton' and f.tier==0 for f in facts))
        self.assertTrue(all(f.tier==0 for f in facts))

    def test_override_uses_current_requirements_only(self):
        state=apply_user_message(IntentState(),"I'm looking for shirts. A key requirement is: Color: black.",1)
        state=apply_user_message(state,'Make that white instead; black is no longer what I want.',2)
        self.assertEqual(query_atoms(state),(QueryAtom('color','white'),))

    def test_stale_catalog_and_missing_sidecar_rejected(self):
        self.catalog.write_text(self.catalog.read_text()+'\n')
        with self.assertRaises(ValueError): AttributeIndex(self.path,self.catalog)
        with self.assertRaises(Exception): AttributeIndex(self.path.with_name('missing.sqlite'),self.catalog)

    def test_negative_and_positive_query_atoms(self):
        state=IntentState(requirements=(Requirement('blue cotton shirts under $50','free_text',1),),excluded=('polyester',))
        self.assertEqual(set(query_atoms(state)),{QueryAtom('color','blue'),QueryAtom('material','cotton'),QueryAtom('material','polyester',-1)})

    def test_counterevidence_only_does_not_reward_better_documentation(self):
        atom=QueryAtom('material','cotton')
        self.assertEqual(self.index.rerank(('c','a'),(atom,),counterevidence_only=True),('c','a'))
        self.assertEqual(self.index.rerank(('b','c','a'),(atom,),counterevidence_only=True),('c','a','b'))

    def test_uncertain_language_does_not_generate_positive_evidence(self):
        state=IntentState(requirements=(Requirement('Maybe blue instead of black','free_text',1),))
        self.assertEqual(query_atoms(state),())

    def test_double_negation_and_substrings_are_not_affirmative_facts(self):
        self.assertEqual(extract_facts({'title':'not cotton-free blueberry-colored'}),())

    def test_free_shipping_is_not_material_negation(self):
        facts=extract_facts({'title':'Cotton free shipping'})
        self.assertEqual([(f.value,f.polarity) for f in facts],[('cotton',1)])

    def test_candidate_only_reorders_the_best_tier_and_preserves_protocol_path(self):
        from conversational_search.exact_evidence import rank_exact_evidence
        from conversational_search.protocol import build_product_protocol_evidence
        from conversational_search.service import _ExactRankingContext
        from scripts.attribute_candidate import AttributeAgent, Baseline
        products=[{'parent_asin':asin,'title':'cotton shirt','categories':['Shoes'],
                   'features':['cotton','color: blue'],'details':details}
                  for asin,details in [('x',{}),('y',{'Material':'cotton'})]]
        products.append({'parent_asin':'z','title':'leather','categories':['Shoes'],'features':['leather']})
        catalog=Path(self.tmp.name)/'tier.jsonl'
        catalog.write_text(''.join(json.dumps(p)+'\n' for p in products))
        path=Path(self.tmp.name)/'tier.sqlite';build_attribute_index(catalog,path)
        index=AttributeIndex(path,catalog);self.addCleanup(index.close)
        ids=('x','y','z');state=IntentState(category='Shoes',requirements=(Requirement('cotton','initial_explicit',1,'material'),))
        evidence=tuple(build_product_protocol_evidence(p) for p in products)
        result=rank_exact_evidence(ids,evidence,state)
        self.assertEqual({b.parent_asin for b in result.beliefs},{'x','y'})
        context=_ExactRankingContext(ids,evidence,result,result.ranked_ids,True)
        agent=object.__new__(AttributeAgent)
        agent._attribute_index=index;agent._attribute_natural=True
        agent._attribute_counterevidence_only=False
        agent.research_diagnostics={'interventions':0,'eligible_ties':0,'errors':0}
        with patch.object(Baseline,'_apply_exact_evidence_ranking',return_value=context):
            revised=agent._apply_exact_evidence_ranking(state,ids)
            self.assertEqual(revised.output_ranked_ids,('y','x','z'))
            self.assertEqual([b.parent_asin for b in revised.result.beliefs],['y','x'])
            self.assertEqual(set(revised.result.consistent_support_ids),set(result.consistent_support_ids))
            agent._attribute_natural=False
            self.assertIs(agent._apply_exact_evidence_ranking(state,ids),context)
            agent._attribute_natural=True;agent._attribute_index=None
            self.assertIs(agent._apply_exact_evidence_ranking(state,ids),context)
        self.assertEqual(agent.research_diagnostics['errors'],0)
