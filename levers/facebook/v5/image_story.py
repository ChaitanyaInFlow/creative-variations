import random
import logging
from typing import Dict, List
from ds.process.cluster_text import ClusterText

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

class ImageStory:
    def __init__(self, discard_ratio: int = .2 ) -> None:
        self.discard_ratio = discard_ratio
        
    def pre_process(self, input_dict) -> Dict:
        story_input = dict()
        layer_order = []
        for lever_output in input_dict:
            layer_dict = lever_output[0]
            layer_name = layer_dict['layer_name'][0]
            if len(layer_dict['layer_name']) == 1:
                if layer_dict['layer_text']:
                    story_input[layer_name] = layer_dict['layer_text']
                else:
                    story_input[layer_name] = layer_dict['original_text']
                layer_order.append(layer_name)
            else :
                if len(layer_dict['layer_text']) == 0:
                    layer_dict['layer_text'] = [' * '.join(layer_dict['original_text'])]
                      
                story_input[layer_name] = layer_dict['layer_text']
                layer_order = layer_order + layer_dict['layer_name']                
        self.layer_order = layer_order
        return story_input       
                
    
    def get_bundles(self, input_dict) -> List:
        story_input = self.pre_process(input_dict)                
        primary_layer = []      
        
        for key in story_input : 
            if primary_layer == []:
                primary_layer = story_input[key]
                primary_layer, _ = ClusterText().get_unique_sentences(primary_layer)
                if (len(primary_layer)<10) and (len(list(story_input.keys()))>1):
                    primary_layer = random.choices(primary_layer, k = 10)
                continue
                
            layer, _ = ClusterText().get_unique_sentences(story_input[key])               
            if len(layer) < 10:
                # layer = random.choices(layer, k = 10)
                layer = list((layer) * 10)[:10]
                                    
            bundle_list = []
            for text in primary_layer:
                                
                if layer:
                    layer = ClusterText().get_matches_sorted(
                        ref_ad=text,
                        generations_list=layer,
                        discard_ratio=self.discard_ratio,
                        generation_type='layer')
                    if layer:
                        bundle_list.append({
                            'primary_layer' : text,
                            'layer' : layer.pop(0)
                        })
                        
            primary_layer = [bundle['primary_layer'] + ' [SEP] ' + bundle['layer'] for bundle in bundle_list]
                    
        output = self.output_formatting(primary_layer)
        print(output)
        if (len(output) < 3):
            output = random.choices(output, k = 3)
        return output
        
    
    def output_formatting(self , raw_story) -> List:
        output = []
        c = 0
        for story in raw_story:
            story_split = story.split(" [SEP] ")
            story_bundle = []
            for text in story_split:          
                if '*' in text:
                    text_split = text.split(" * ")
                    for phrase in text_split:
                        layer_dict = {}
                        layer_dict['layer_name'] = self.layer_order[c]
                        layer_dict['layer_text'] = phrase.strip()
                        story_bundle.append(layer_dict)
                        c += 1
                else :
                    layer_dict = {}
                    layer_dict['layer_name'] = self.layer_order[c]
                    layer_dict['layer_text'] = text.strip()
                    story_bundle.append(layer_dict)
                    c+=1
            output.append(story_bundle)
            c = 0
                    
        return output


def story_v5(input_dict):
    logging.debug("fb image_story: get_bundles started")
    bundle_list= ImageStory().get_bundles( input_dict
    )
    logging.debug("fb image_story: get_bundles completed")
    return bundle_list


if __name__ == "__main__":
    print("###############")
    #input = [[{'layer_name': ['Text 1', 'Text 2', 'Text 3'], 'original_text': ['GET MEALS FOR', ' $4.99 / MEAL', '+ FREE SHIPPING'], 'layer_text': []}]]
    input = [[{'layer_name': ['Text 1', 'Text 2'], 'original_text': ['The credit card', 'no annuity'], 'layer_text': ['Fast Line Of Credit  *  No Hassle', 'Instant Access  *  To Funds', 'Instant Credit  *  No Annuity', 'Instant Credit  *  With Klar', 'Get Credit Now  *  With Klar', 'No Annuity Card *  From Klar', 'Quick & Easy Credit *  From Klar', 'Rapid Credit Line  *  Hassle Free']}]]
    bundles = story_v5(input)
    print(bundles)