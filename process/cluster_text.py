import random
import numpy as np
from thefuzz import fuzz
from typing import List, Dict

class ClusterText:
    '''
    This class clusters the given set of input senetences

    Attributes:
        threshold (int): threshold to find similarity between sentences in a cluster
        similarity between any two sentences in a cluster to be more than the threshold attribute
    '''
    
    def __init__(self, threshold :int = 80) -> None:
        '''
        The constructer for ClusterText class
        
        Parameters:
            threshold (int): threshold to find similarity between sentences in a cluster
            similarity between any two sentences in a cluster to be more than the threshold attribute
        '''
        self.threshold = threshold

    def get_unique_clusters(self, input_assets: List[Dict], similarity: str='partial'):
        '''
        This function to cluster the given sentences
        
        Parameters:
            input_assets (List[Dict]): [{"text" : Sentenece1}, {"text" : Sentenece2}]

        Returns:
            cluster (List[List[Dict]]): [
                [{"text" : Sentenece1}, {"text" : Sentenece2}],
                [{"text" : Sentenece3}, {"text" : Sentenece4}],
                ..
                ]
        '''
        if input_assets == None:
            return {}
        input_asset_count = len(input_assets)
        fuzz_similarity_mat = np.zeros((input_asset_count, input_asset_count))
        for row_idx in range(input_asset_count):
            for col_idx in range(input_asset_count):
                fuzz_similarity_mat[row_idx][col_idx] = fuzz.partial_ratio(input_assets[row_idx]['text'], input_assets[col_idx]['text'])
        
        ## [-1,1,1,3,3] -> similar asset list [1st asset] [2nd asset, 3rd asset], [4th asset, 5th asset]
        ## initialise list with -1 and override with index with similarity more than the threshold
        similar_asset_idx_list = [-1]*input_asset_count
        for row_idx in range(input_asset_count):
            if similar_asset_idx_list[row_idx] == -1:
                similar_asset_idx_list[row_idx] = row_idx
                
            current_group_idx = similar_asset_idx_list[row_idx]
            for col_idx in range(row_idx+1, input_asset_count):
                if fuzz_similarity_mat[row_idx][col_idx] > self.threshold:
                    similar_asset_idx_list[col_idx] = current_group_idx # [0,1,-1]

        clusters = []
        for group_idx in range(input_asset_count):
            similar_group_sentences = [input_assets[idx] for idx in range(group_idx, input_asset_count) if similar_asset_idx_list[idx] == group_idx]
            if similar_group_sentences:
                clusters.append(similar_group_sentences)

        return clusters

    def get_unique_sentences(self, input_assets: List[str]):
        '''
        This function returns a list of unique sentences for a given list of sentences
        Clusters given sentences and from each cluster randomly picks one sentenece
        
        Parameters:
            input_assets (List[str]): list of sentences

        Returns:
            List[str] : list of unique sentences
            List[str] : list of discarded sentences from all the input sentences
        '''
        input_assets = [{"text" : asset} for asset in input_assets]
        clusters = self.get_unique_clusters(input_assets)

        unique_sentenes, discarded_sentences = [], []
        for cluster in clusters:
            unique_sentenes.append(cluster.pop(random.randrange(len(cluster)))['text'])
            discarded_sentences.extend([sent['text'] for sent in cluster])
        return unique_sentenes, discarded_sentences

    def get_unique_assets_by_filter_key(self, input_assets: List[Dict], filter_key: str ='performance_probabilities'):
        '''
        This function returns a list of unique sentences for a given list of sentences
        Clusters given sentences and from each cluster picks one sentenece by the given key
        
        Parameters:
            input_assets (List[Dict]): [
                {
                    "text" : Sentenece1, 
                    "performance" : "High"
                    }, 
                {
                    "text" : Sentenece2,
                    "performance" : "Low"
                    },
                ...]

        Returns:
            List[Dict] : list of unique assets
            List[Dict] : list of discarded assets from all the input assets
        '''
        clusters = self.get_unique_clusters(input_assets)
        unique_assets, discarded_assets= [], []
        for cluster in clusters:
            shortlisted_asset = max(cluster, key=lambda x:x[filter_key])
            cluster.remove(shortlisted_asset)
            unique_assets.append(shortlisted_asset)
            discarded_assets.extend([cluster])
        unique_assets.sort(key=lambda x:x[filter_key], reverse=True)
        return unique_assets, discarded_assets

    def get_matches_sorted(self, ref_ad: str, generations_list: List[Dict], discard_ratio: int=.2, generation_type: str=str):
        '''
        This function checks the similarity between given reference and list of sentences
        Very similar sentences are penalised 
        Parameters:
            ref_ad (str): input_string
            generations_list (List[Dict]) : list of dicts for sorting 
            discard ratio :  peanalisation ratio for very simiar sentences
        '''
        # Give Weightage to lengthy description and penalize similar discriptions
        if generation_type == 'layer':
            ref_ad = {"text": ref_ad}
            generations_list = [{"text": generation} for generation in generations_list]
        fuzz_ratio_tuple_list = [(generation, (generation.get('performance_probabilities', 1)*len(generation['text']))/max(fuzz.partial_ratio(ref_ad, generation['text']), 1)) for generation in generations_list]
        sorted_fuzz_tuple_list = sorted(fuzz_ratio_tuple_list, key=lambda x: x[1], reverse=True)
        # Discard top ranked discriptions
        discard_top_match_list = sorted_fuzz_tuple_list[round(discard_ratio*len(sorted_fuzz_tuple_list)):] + sorted_fuzz_tuple_list[:round(discard_ratio*len(sorted_fuzz_tuple_list))]
    
        if generation_type == 'layer':
            return [gen_tuple[0]['text'] for gen_tuple in  discard_top_match_list]
        else:
            return [gen_tuple[0] for gen_tuple in discard_top_match_list]


if __name__ == "__main__":
    sample_gens = ["Alert: Back in Stock! We heard you missed us so we restocked our most-wanted pieces for you. Grab 'em while stock lasts. Hurry!",
                    "Spring's here! Look eyeconic in trendy textures and revamped classics from our #JJSafari edit. Shop the limited edition now!",
                    'Hit the re-style button! Add glamour into your wardrobe with our striking and structured steelworks. Shop now!',
                    'Our biggest hits, now available at wow prices! Strike a pose in chic eyewear and update your look for an unforgettable summer.',
                    'Life imitates art with our CreatorShop curation! Shop eyewear outfitted with printed details and intricate design elements.',
                    'Strike a pose in the coolest summer fashion! Browse our uber-chic range of sunglasses to strut in style this season. Visit now!',
                    "Gift mom a stylish new view! Shop our Mother's Day Sale for unmissable offers on uber-chic eyewear. Browse our edit now",
                    "Gift mom a stylish new view! Shop our Mother's Day Sale for unmissable offers on uber-chic eyewear. Browse our edit now",
                    'Looking for the coolest summer trends? Browse our latest drop of chunky acetates and chiselled frames for an upgrade! Shop now.',
                    'Eye-fashion at its best! Strike a pose in our master metalworks and add a touch of glamour to your look. Shop now!',
                    "Summer's calling! Jet-set in style this season with our latest collection of sunset-worthy shades and uber-fresh tints. Shop now.",
                    'Hey gamers! Spending long hours perfecting your score? Armor up in our Zero Power BLU Lenses & block the digital glare.',
                    "Looking for a stylish gift for dad? Say 'Happy Father's Day' with John Jacobs' special SALE. Shop our eye-poppin' offers now!",
                    'Looking to make a great escape? Flee to stunning vistas with our latest edition, JJ Voyage! Shop uber-fresh tints now.',
                    "This International Yoga Day, go for the ultimate flex! Shop our dynamic TR Flex frames for eye-poppin' prices. Visit now.",
                    'Looking to make a great escape? Flee to stunning vistas with our latest edition, JJ Voyage! Shop uber-fresh tints now.',
                    "Shop the best deals on iconic eye-fashion with JJ's End Of Season Sale! 👀",
                    'Our latest collection, Roman Holiday, is a sight to behold! Fall in love with delicate textures and ornate details. Shop now!',
                    'Striking gold accents, rich colours and romantic textures. The Roman Holiday Edit by John Jacobs is here. Shop now.',
                    "John Jacobs - The best in business"
                    ]
    sample_brand = 'John Jacobs'
    cluster_obj = ClusterText()
    clusters = cluster_obj.get_unique_sentences([{"text": gen, "performance_probability": .9} for gen in sample_gens])
    print(clusters)