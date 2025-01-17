
import sys
import traceback

from ds.lever import Lever


class HeadlineOffer(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
            {
                "role": "system", 
                "content": '''You are a helpful digital marketing assistant for writing creative Facebook ad Headlines for the given Brand Info, Interest Keyword and Offer

Don't use hyphen in the Headlines.
Each Headline must contain the Offer and the Interest Keyword.

Follow the Examples.'''},
            {
                "role": "user", 
                "content": f'''###
Example 1
Brand: Swiggy is a food ordering and delivery platform. It helps users order food from their favorite restaurants near them and track their delivery partner till their food is delivered.
Interest Keyword: <<Pizza>>
Offer: 20% off
Write 5 Headlines. Each Headline must be less than 8 words. Each Headline must contain the Offer. Don't use hyphen in the Headlines
Headline 1: 20% Off On Your First <<Pizza>> Order
Headline 2: Get <<Pizza>> From Swiggy @20% Off
Headline 3: Get Your Favorite <<Pizza>> With 20% Off
Headline 4: <<Pizza>> At 20% Off With Swiggy
Headline 5: Treat Yourself To <<Pizza>> With 20% Off 
###
Example 2
Brand: Livspace is an interior design startup that offers a platform that connects people to designers, services, and products. With a variety of interior designs to choose from, Livspace makes it easy for customers to get the exact look they want for their homes.
Interest Keyword: <<Modular Kitchens>>
Offer: EMIs
Write 6 Headlines. Each Headline must be less than 8 words. Each Headline must contain the Offer. Don't use hyphen in the Headlines
Headline 1: Italian <<Modular Kitchens>> On EMIs
Headline 2: Compact <<Modular Kitchens>>, Easy EMIs
Headline 3: Get Your Dream <<Modular Kitchen>> On EMIs
Headline 4: Flexible EMI Plans On <<Modular Kitchens>>
Headline 5: EMI Options On <<Modular Kitchens>>
Headline 6: Easy EMIs For Your <<Modular Kitchen>>
###
Example 3
Brand: Allbirds, Inc. is a New Zealand-American company that sells footwear and apparel. They crafted a revolutionary wool fabric made specifically for footwear. Products include Shoes, Apparel, Accessories.
Interest Keyword: <<Shoes>>
Offer: 30 days return
Write 2 Headlines. Each Headline must be less than 8 words. Each Headline must contain the Offer. Don't use hyphen in the Headlines
Headline 1: 30 Days Return On Allbirds <<Shoes>>
Headline 2: <<Shoes>> With 30 Days Return Policy
###
Example 4
Brand: {self.input_dict['bu_detail']}
Interest Keyword: <<{self.input_dict['interest_keyword']}>>
Offer: {self.input_dict['offer_used']}
Write 10 Headlines. Each Headline must be less than 8 words. Each Headline must contain the Offer. Don't use hyphen in the Headlines
Headline 1:'''
        }]
        self.nlg_parameters = {
            "n": 3,
            "top_p": 1,
            "temperature": 1,
            "response_length": 300,
            "presence_penalty": 0,
            "frequency_penalty": 0
        }

        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)


    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation_list = generation.split('\n')
            for i in range(len(generation_list)):
                generation_list[i] = generation_list[i].replace('Headline ' + str(i+1) + ':', '')
            self.extracted_generations += generation_list


    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=False)
        self.post_process_list = []
        for generation in self.extracted_generations:
            self.post_process_list.append(post_process_obj.run(generation, self.input_dict))

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(
            max_length=50, 
            min_length=20, 
            threshold=84)
        self.filtered_list, self.log_json['discard_filter_generations'] = filter_obj.run(
            self.post_process_list, 
            reference_ad='',
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
            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()
            final_outputs_needed = input_dict['n_generations']
            return self.performance_generations_dict_list[:final_outputs_needed],  self.log_json
            
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
            "reference_primary_text": "Dapat bayaran dalam 24 jam",
            "n_generations": 5,
            "offer_used": "2.3% Off"
            }
    gens, logs = HeadlineOffer().run(id)
    print([gen['text'] for gen in gens])
