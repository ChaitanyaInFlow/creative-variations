import sys
import traceback
import os
import yaml
from ds.lever import Lever

from ds.scripts.detect_language import detect_language

class HeadlineParaphrase(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        
        input_reference_primary_text = self.input_dict.get('reference_primary_text','')
        input_reference_description = self.input_dict.get('reference_description','')
        input_additional_reference = ''

        if input_reference_description:
            if (input_reference_description[-1] not in ['.','!','?']):
                input_reference_description += '. '
            input_additional_reference += input_reference_description

        if input_reference_primary_text:
            if (input_reference_primary_text[-1] not in ['.','!','?']):
                input_reference_primary_text += '. '
            input_additional_reference += input_reference_primary_text

        self.input_dict['additional_reference'] = input_additional_reference
        ## Detect Language
        text = " ".join([self.input_dict['reference_headline'], input_additional_reference])
        self.input_dict['language'] = detect_language(text)


        ## Compliance
        additional_instructions, replacement_instructions = '', ''
        brand_id = self.input_dict.get('brand_id', '')
        compliance_file_path = 'ds/process/brand_specific/' + str(brand_id) + '.yaml'
        if os.path.exists(compliance_file_path):
            with open(compliance_file_path, "r") as f:
                data = yaml.safe_load(f) 
            additional_instructions = data.get('additional_instructions')
            replacement_instructions = data.get('replacement_instructions')
           
        self.prompt = [
            {
                "role": "system", 
                "content": f'''You are a helpful digital marketing assistant for writing creative Facebook ad Headlines for the given Brand Info, Reference Headline and Additional Reference
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''} '''},
                            {
                "role": "user", 
                "content": f'''Write creative Facebook ad Headlines for the given Brand Info, Reference Headline and Additional Reference.

###
Example 1
Brand Info: Allbirds, Inc. is a New Zealand-American company that sells footwear and apparel. They crafted a revolutionary wool fabric made specifically for footwear. Products include Shoes, Apparel, Accessories.
Reference Headline: Free Shipping + Free Returns.
Additional Reference: Made to get outside, move, and be ridiculously comfortable. Comfy? Check. Planet-friendly? Check. Everyday styles for any kind of day.

Write 6 Variations of the Reference Headline using context from the Brand Info and Additional Reference. All Variations must be less than 40 characters.

Variation 1: Comfy & Planet-Friendly Styles
Variation 2: Get Outside & Enjoy Comfort
Variation 3: Move In Style With Allbirds
Variation 4: Shop Free Shipping & Returns
Variation 5: Shop Allbirds Shoes & Apparel
Variation 6: Free Shipping on Allbirds

###
Example 2
Brand Info: HelloFresh is the first global carbon-neutral meal kit company, supporting global and local environmentally-friendly projects you care about.
Reference Headline: Rethink every meal, and save! 
Additional Reference: Come Back for $150 Off. Stuck on what to have for dinner? Say hello to tasty dishes and farm-fresh ingredients, delivered right to your door!

Write 6 Variations of the Reference Headline using context from the Brand Info and Additional Reference. All Variations must be less than 40 characters.

Variation 1: Reimagine Dinner Time With HelloFresh
Variation 2: Get Tasty Dishes With HelloFresh
Variation 3: Tasty Dinner With Farm-Fresh Ingredients
Variation 4: Sustainable Meals With HelloFresh
Variation 5: Rethink Dinners, Save Big!
Variation 6: Get $150 Off With HelloFresh

###
Example 3
Brand Info: {self.input_dict['bu_detail']}
Reference Headline: {self.input_dict['reference_headline']}
Additional Reference: {self.input_dict['additional_reference']}

Write 6 Variations of the Reference Headline using context from the Brand Info and Additional Reference. All Variations must be less than 30 characters.
All Variations must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}

Variation 1:'''
}]
        self.nlg_parameters = {
            "n": 3,
            "top_p": 1,
            "temperature": 0.8,
            "response_length": 250,
            "presence_penalty": 1,
            "frequency_penalty": 1
        }
        if self.input_dict['language'] != 'English':
            self.nlg_parameters['temperature'] = 0.7
            self.nlg_parameters['presence_penalty'] = 0
            self.nlg_parameters['frequency_penalty'] = 0

        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)
        return
    
    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        ## Strip Generations starting with Variant 1, Variant 2, etc or Variation 1, Variation 2, etc.
        for generation_str in self.nlg_generations_list:
            generation_list = generation_str.split('\n')

            stripped_generations_list = []
            for generation in generation_list:
                generation = generation.strip()
                if generation.lower().startswith('varia'):
                    stripped_generation = ' '.join(generation.split()[2:])
                    stripped_generations_list.append(stripped_generation)

            self.extracted_generations += stripped_generations_list


    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict['language'] == 'English':
            post_process_obj = self.postprocess_class(title_case=True, ending_exclusions='.!', exclude_domain=True, exclude_phone_number=True)
            self.post_process_list = []
            for generation in self.extracted_generations:
                self.post_process_list.append(post_process_obj.run(generation, self.input_dict, reference_input=self.input_dict['reference_headline'], separator=''))
        else:
            self.post_process_list = self.extracted_generations
        return
    
    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        #min_length=self.min_length, max_length=50
        filter_obj = self.filter_generations_class(max_length= max(len(self.input_dict['reference_headline']), 50) , min_length=15, threshold=84)
        self.filtered_list, self.log_json['discard_filter_generations'] = \
            filter_obj.run(
                self.post_process_list, 
                reference_ad = self.input_dict['reference_headline'], 
                input_dict=self.input_dict,
                check_english= False if self.input_dict['language']!='English' else True)
        self.log_json['filtered_generations'] = self.filtered_list

        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filtered_list)
        self.log_json['performance_labels'] = self.performance_list
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)
        
    @Lever.log_run
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()
            final_outputs_needed = input_dict['n_generations']
            return self.performance_generations_dict_list[:final_outputs_needed], self.log_json
            
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return [], updated_log_json 

if __name__ == '__main__':
    id = {
            "reference_headline": "You'll wear these daily",
            "bu_name": "Vuori",
            "bu_detail": "Vuori is a premium performance apparel brand inspired by the active Coastal California lifestyle. The brand offers apparel that is ethically manufactured and made with durable performance materials.",
            "brand_name": "Vuori",
            "interest_keyword": "apparel",
            "n_generations": 6,
            "limit": 40,
            "reference_description": "You'll wear these daily!",
            "reference_primary_text": "You'll wear these daily.",
            "additional_reference": "You'll wear these daily!You'll wear these daily.",
            "language": "English"
                    }
    id1 = {
        "bu_detail" : '''HIMS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        "reference_primary_text": '''Join healthcare professionals, technology providers and government representatives as we look at the transformation of healthcare across the region.''',
        "reference_headline": 'Manifest transformative health tech at HIMS.',
        "reference_description": 'Get prescription fast',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        # "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7_",
        "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
        "n_generations" : 6,
        "language": "English"
    }

    id2 = {
        "bu_detail" : '''HIMS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        "reference_primary_text": '''Join healthcare professionals, technology providers and government representatives as we look at the transformation of healthcare across the region.''',
        "reference_headline": 'Manifest transformative health tech at HIMS.',
        "reference_description": 'Get prescription fast',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7",
        # "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
        "n_generations" : 6,
        "language": "English"
    }

    id3 = {
        "bu_detail" : '''HIMS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        "reference_primary_text": '''Join healthcare professionals, technology providers and government representatives as we look at the transformation of healthcare across the region.''',
        "reference_headline": 'Manifest transformative health tech at HIMS.'.upper(),
        "reference_description": 'Get prescription fast',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7_",
        # "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
        "n_generations" : 6,
        "language": "English"
    }

    id3 = {
        "bu_name": "Claro Shop",
        "brand_id" : "112811d5-d614-40ce-bcec-8d3945262e2f",
        # "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
        "n_generations" : 6,

        "bu_detail": "Claro Shop is an e-commerce website that sells electronic gadgets, kitchen appliances, furniture, apparel, footwear, and gym utilities.", 
        "brand_name": "Claro Shop", 
        "interest_keyword": "e-commerce",
          "reference_headline": "¡Solicítalo ahora!", 
          "reference_description": "", 
          "reference_primary_text": "Estrena millones de productos este Hot Sale a meses, sin tarjeta, sin aval con tu Crédito Claro Shop :fire::fire: Disfruta 15% de descuento adicional en tu primer compra + hasta 24 meses :star-struck:"
    }
    


    # ids = [id1, id2, id3]
    ids = [id3]
    gen_list = []

    for id in ids:
        gens, logs = HeadlineParaphrase().run(id)
        gen_list.append("\n".join([gen['text'] for gen in gens]))
    print("$$$")

    for gen in gen_list:
        print("\n\n######\n\n")
        print(gen)

