import random
import logging
from collections import OrderedDict
from ds.process.filter import FilterGenerations
from ds.process.cluster_text import ClusterText
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')
class VideoStory:
    def __init__(self, discard_ratio = .2 ) -> None:
        self.discard_ratio = discard_ratio
        
    def pre_process(self, input_dict) -> dict:
        
        story_input = OrderedDict()
        self.layer_order = []
        
        for lever_output in input_dict:
            
            layer_dict = lever_output[0]
            layer_name = layer_dict['layer_name'][0]
            # Flow for cases when length of list layer_dict[layer_name] is 1 and more than 1
            if len(layer_dict['layer_name']) == 1:
                #for full sentence lever                    
                if layer_dict['layer_text']:
                    story_input[layer_name] = layer_dict['layer_text']                    
                else:
                    #if no generations , use original text
                    story_input[layer_name] = layer_dict['original_text']                          
                self.layer_order.append([layer_name,layer_dict['frame_name'][0]])
                
            else :
                #for partial sentence lever
                if len(layer_dict['layer_text']) == 0:
                    layer_dict['layer_text'] = [' * '.join(layer_dict['original_text'])]
                        
                story_input[layer_name] = layer_dict['layer_text']
                self.layer_order = self.layer_order + [[layer_name,frame_name] for layer_name, frame_name in zip(layer_dict['layer_name'],layer_dict['frame_name'])]            
        return story_input       
                
    
    def get_bundles(self, input_dict) -> list:
        
        story_input = self.pre_process(input_dict)
                
        primary_layer = []              
        for key in story_input :     
            ## Storing sccuessive layer data in primary_layer. If lenght of primary layer is less than 10, we randomize the selections to 10
            if primary_layer == []:
                primary_layer = story_input[key]
                primary_layer, _ = ClusterText().get_unique_sentences(primary_layer)
                # print(primary_layer)
                if (len(primary_layer)<10) and (len(list(story_input.keys()))>1):
                    primary_layer = random.choices(primary_layer, k = 10)
                #print(primary_layer)
                continue
            
            
            layer, _ = ClusterText().get_unique_sentences(story_input[key])               
            if len(layer) < 10:
                # layer = random.choices(layer, k = 10)
                layer = list(layer * 10)[:10]
                    
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
            print('total bundles ', len(primary_layer) )
                   
        output = self.output_formatting(primary_layer)

        if (len(output) < 3):
            output = random.choices(output, k = 3)
        
        return output
        
    
    def output_formatting(self , raw_story) -> None:
        ##Formatting the output of story function to put everything back in its own layer
        output = []
        
        for story in raw_story:
            story_split = story.split(" [SEP] ")
            story_bundle = []
            #decalring variable for keepoing track of layer id  
            layer_counter = 0
            for text in story_split:
                ### for partial sentence. It can have multiple layers so counter needs to be updated 
                if '*' in text:
                    text_split = text.split(" * ")
                    for phrase in text_split:
                        layer_dict = {}
                        layer_dict['layer_name'] = self.layer_order[layer_counter][0]
                        layer_dict['frame_name'] = self.layer_order[layer_counter][1]
                        layer_dict['layer_text'] = phrase.strip()
                        story_bundle.append(layer_dict)
                        layer_counter+=1
                ## for full sentence. It will have single entries
                else :
                    layer_dict = {}
                    layer_dict['layer_name'] = self.layer_order[layer_counter][0]
                    layer_dict['frame_name'] = self.layer_order[layer_counter][1]
                    layer_dict['layer_text'] = text.strip()
                    story_bundle.append(layer_dict)
                    layer_counter+=1
            
            output.append(story_bundle)
            
                    
        return output


def videostory_v5(input_dict):
    logging.debug("fb video_story: get_bundles started")
    bundle_list= VideoStory().get_bundles( input_dict
    )
    logging.debug("fb video_story: get_bundles completed")

    return bundle_list


if __name__ == "__main__":
    print("###############")
    #input = [[{'layer_name': ['Text 1', 'Text 2', 'Text 3'], 'original_text': ['GET MEALS FOR', ' $4.99 / MEAL', '+ FREE SHIPPING'], 'layer_text': []}]]
    input = [[{'layer_name': ['Text 1', 'Text 2'],'frame_name': ['Text 1', 'Text 2'], 'original_text': ['The credit card', 'no annuity'], 'layer_text': ['Fast Line Of Credit  *  No Hassle', 'Instant Access  *  To Funds', 'Instant Credit  *  No Annuity', 'Instant Credit  *  With Klar', 'Get Credit Now  *  With Klar', 'No Annuity Card *  From Klar', 'Quick & Easy Credit *  From Klar', 'Rapid Credit Line  *  Hassle Free']}]]
    bundles = videostory_v5(input)
    print(bundles)





