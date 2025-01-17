import sys
import traceback
import emoji
import logging
import re

from ds.lever import Lever

class PrimaryText(Lever):

    def separate_primarytext_and_listicle(self, primarytext):

        def _is_list_element(line):
            listicle_lenght_thres = 120 # 70 characteres
            
            # if line starts w/ special symbol or emoji and is shorter than threshold
            if len(line) < listicle_lenght_thres \
            and ( emoji.is_emoji(line[0]) or bool(re.search(r'\W', line[0]))):
                return True
            
            else:
                return False

        if not primarytext or type(primarytext) != type('asdf'): return '', ''

        
        lines_list = [el.strip() for el in primarytext.split('\n') if el.strip()]
        
        listicle_elements = []
        for i, line in enumerate(lines_list):
            
            # if line starts w/ special symbol or emoji and is shorter than threshold
            if _is_list_element(line):
                # if previous line was also list element
                if i>0 and _is_list_element(lines_list[i-1]):
                    listicle_elements.append(line)
                
                # or next line is list element
                elif i<len(lines_list)-1 and _is_list_element(lines_list[i+1]):
                    listicle_elements.append(line)

        # print('lines:', lines_list)
        # print('listicles:', listicle_elements)

        reference_plain_primarytext = []
        for line in lines_list:
            if line not in listicle_elements:
                reference_plain_primarytext.append(line)
            else:
                break
                # break when listicle starts

        # print(reference_plain_primarytext)
        reference_plain_primarytext = ' '.join(reference_plain_primarytext)

        reference_listicle = [el for el in lines_list if el not in reference_plain_primarytext]
        reference_listicle = '\n'.join(reference_listicle)
        
        return reference_plain_primarytext, reference_listicle


    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
            {
                "role": "system", 
                "content": "You are a helpful digital marketing assistant for writing creative Facebook ad Primary Text for the given Brand Info, Reference Primary Text and Interest Keyword."},
            {
                "role": "user", 
                "content": f'''###
Example 1
Brand Info: Swiggy is an online food ordering and delivery platform. It helps users order food from their favorite restaurants near them and track their delivery partner.
Reference Primary Text: Get match ready with Swiggy Matchday Mania! Enjoy 50% off + free delivery on your first order.
Interest Keyword: <<pizza>>
Write 5 Variations of the Reference Primary Text for the given Brand Info and Interest Keyword. All Variations must be less than 129 characters.
Variation 1: Swiggy will stump your cravings! Order yummy <<Pizzas>> to get you through all your innings. Grab 50% off on your first order.
Variation 2: Bowl out your cravings with Swiggy. Enjoy cheeseburst <<Pizzas>> at amazing prices. Get free home delivery. Order now
Variation 3: Win the toss with your hunger on Swiggy! Double the cricket mania with cheeseburst <<Pizza>>. 50% off + free home delivery!
Variation 4: Double the cricket craze with Swiggy's <<Pizza>> deals. Choose from 75,000+ restaurants. Avail 50% off & free home delivery.
Variation 5: Calm down your cricket fever with some delicious <<pizza>> from Swiggy! Order now & get 50% discount + free home delivery!
###
Example 2
Brand Info: HelloFresh is a food subscription company that sends pre-portioned ingredients to users. HelloFresh's meal kits include all the ingredients you need to cook a healthy, delicious meal. With HelloFresh, you can choose from a variety of recipes and meals, and the company delivers them to you 
Reference Primary Text: Stuck on what to have for dinner? Say hello to tasty dishes and farm-fresh ingredients, delivered right to your door!
Interest Keyword: <<Vegan Meal kits>>
Write 4 Variations of the Reference Primary Text for the given Brand Info and Interest Keyword. All Variations must be less than 129 characters.
Variation 1: Say hello to HelloFresh! With our delicious <<vegan meal kits>>, you'll never have to worry about what to make for dinner.
Variation 2: Dinner's sorted! HelloFresh's <<vegan meal kits>> are packed with tasty, farm-fresh ingredients that will make your mouth water.
Variation 3: Looking for a <<vegan meal kit>>? With HelloFresh's easy-to-follow recipes, you'll have a yummy meal on the table in no time.
Variation 4: Tired of the same old dinner? With HelloFresh's variety of <<vegan meal kits>>, try new recipes, delivered right to your door.
###
Example 3
Brand Info: {self.input_dict['bu_detail']}
Reference Primary Text: {self.input_dict['refrence_plain_primary_text']}
Interest Keyword: <<{self.input_dict['interest_keyword']}>>
Write 8 Variations of the Reference Primary Text for the given Brand Info and Interest Keyword. All Variations must be less than 129 characters.
Variation 1:'''
            }]

        self.nlg_parameters = {
            "n": 3,
            "top_p": 1,
            "temperature": 1,
            "response_length": 500,
            "presence_penalty": 0.8,
            "frequency_penalty": 0.6
        }

        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation_list = generation.split('\n')
            for i in range(len(generation_list)):
                generation_list[i] = generation_list[i].strip()
                if(len(generation_list[i])>0):
                    if(generation_list[i].split()[0].lower() in ["variation", "variant"]):
                        gen_list = generation_list[i].split()[2:]
                        generation_list[i] = " ".join(gen_list)

            self.extracted_generations += generation_list

    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=False, exclude_exclamation=False, ending_exclusions='')
        self.post_process_list = []
        for generation in self.extracted_generations:
            self.post_process_list.append(post_process_obj.run(generation, self.input_dict))
        self.log_json['post_process_list'] = self.post_process_list


    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(
            max_length=250, 
            min_length=50, 
            threshold=84)
        self.filtered_list, self.log_json['discard_filter_generations'] = filter_obj.run(
            self.post_process_list, 
            reference_ad = self.input_dict['refrence_plain_primary_text'],
            input_dict=self.input_dict)
        self.log_json['filtered_generations'] = self.filtered_list
        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filtered_list)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.discarded_list = cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)

    @Lever.log_run
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            self.input_dict['original_reference_primary_text'] = self.input_dict['refrence_plain_primary_text']
            reference_primary_text, reference_listicle = self.separate_primarytext_and_listicle(self.input_dict['refrence_plain_primary_text'])
            self.input_dict['refrence_plain_primary_text'] = reference_primary_text

            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()

            # n_gen is the value that core sends to us referring to how many outputs they want to be displayed
            final_outputs_needed = input_dict['n_generations']
            
            return self.performance_generations_dict_list[:final_outputs_needed] ,  self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return [], updated_log_json 
   

if __name__ == '__main__':
    id = {
            "bu_name": "Carsome",
            "bu_detail": "Carsome is an online car-selling platform that connects customers to used car dealers. The company offers a range of services, including car inspection, ownership transfer, and financing. It also offers a curated selection of cars to individuals who wish to buy pre-owned cars.",
            "brand_name": "Carsome",
            "interest_keyword": "Investment",      
            "reference_headline": "KONFEM LAJU",
            "reference_description": "Dapat bayaran dalam 24 jam",
            "refrence_plain_primary_text": "Dapat bayaran dalam 24 jam",
            "n_generations": 5
            }
    id = {
            "reference_headline": "You'll wear these daily",
            "bu_name": "Vuori",
            "bu_detail": "Vuori is a premium performance apparel brand inspired by the active Coastal California lifestyle. The brand offers apparel that is ethically manufactured and made with durable performance materials.",
            "brand_name": "Vuori",
            "interest_keyword": "apparel",
            "n_generations": 6,
            "limit": 40,
            "reference_description": "You'll wear these daily!",
            "refrence_plain_primary_text": "You'll wear these daily.",
            "additional_reference": "You'll wear these daily!You'll wear these daily.",
            "language": "English"
                    }
    gens, logs = PrimaryText().run(id)
    print(gens)
