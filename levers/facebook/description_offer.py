import sys
import traceback

from ds.lever import Lever

class DescriptionOffer(Lever):

    @Lever.log_generate
    def generate(self) -> None:

        self.prompt = [
            {
                "role": "system", 
                "content": '''You are a helpful digital marketing assistant for writing creative Facebook ad Descriptions for a given Brand, Interest Keyword and Offer. 

Don't use hyphen in the Descriptions.
Each Description must contain the Offer.'''},

            {
                "role": "user", 
                "content": f'''###
Generation 1
Brand: Carsome is an online used car platform that provides efficient car buying services to individuals and entities. Through its online bidding portal, customers are able to buy vehicles directly from the dealers.
Interest Keyword: <<Jeep>>
Offer: 1 Year Warranty
Write 3 Descriptions. Each Description must be less than 8 words. Each Description must contain the Offer. Don't use hyphen in the Descriptions
Description 1: 1 Year Warranty on All <<Jeep>> Deals!
Description 2: Warranty on <<Jeep>> Deals for 1 Year!
Description 3: 1 Year Warranty From Carsome on <<Jeep>>
###
Generation 2
Brand: Livspace is an interior design startup that offers a platform that connects people to designers, services, and products. With a variety of interior designs to choose from, Livspace makes it easy for customers to get the exact look they want for their homes.
Interest Keyword: <<Modular Kitchens>>
Offer: EMIs
Write 6 Descriptions. Each Description must be less than 8 words. Each Description must contain the Offer. Don't use hyphen in the Descriptions
Description 1: Italian <<Modular Kitchens>> On EMIs
Description 2: Compact <<Modular Kitchens>>, Easy EMIs
Description 3: Get Your Dream <<Modular Kitchen>> on EMIs
Description 4: Flexible EMI Plans on <<Modular Kitchens>>
Description 5: EMI Options on <<Modular Kitchens>>
Description 6: Easy EMIs for Your <<Modular Kitchen>>
###
Generation 3
Brand: Allbirds, Inc. is a New Zealand-American company that sells footwear and apparel. They crafted a revolutionary wool fabric made specifically for footwear. Products include Shoes, Apparel, Accessories.
Interest Keyword: <<Shoes>>
Offer: 30 days return
Write 2 Descriptions. Each Description must be less than 8 words. Each Description must contain the Offer. Don't use hyphen in the Descriptions
Description 1: 30 days return on Allbirds <<Shoes>>
Description 2: <<Shoes>> with 30 days Return Policy
###
Generation 4
Brand: {self.input_dict['bu_detail']}
Interest Keyword: <<{self.input_dict['interest_keyword']}>>
Offer: {self.input_dict['offer_used']}
Write 10 Descriptions. Each Description must be less than 8 words. Each Description must contain the Offer. Don't use hyphen in the Descriptions
Description 1:'''
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
        return

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation_list = generation.split('\n')
            for i in range(len(generation_list)):
                generation_list[i] = generation_list[i].replace('Description ' + str(i+1) + ':', '')
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
            final_output = self.performance_generations_dict_list[:final_outputs_needed]
            return final_output, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return [], updated_log_json
   
if __name__ == "__main__":
    id = {
            "bu_name": "Carsome",
            "bu_detail": "Carsome is an online car-selling platform that connects customers to used car dealers. The company offers a range of services, including car inspection, ownership transfer, and financing. It also offers a curated selection of cars to individuals who wish to buy pre-owned cars.",
            "brand_name": "Carsome",
            "interest_keyword": "Investment",  
            "offer_used": "20% off",   
            "reference_headline": "Cars at best price",
            "reference_description": "Invest in cars to get better future",
            "reference_primary_text": "Invest in cars to get better future",
            "n_generations": 5
            }
    gens, logs = DescriptionOffer().run(id)
    print(gens)

