
import sys
import traceback

from ds.lever import Lever

class HeadlineInterest(Lever):


    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
            {
                "role": "system", 
                "content": '''You are a helpful digital marketing assistant for writing creative Facebook ad Headlines for the given Brand Info and Interest Keyword

Each Headline must contain the Interest Keyword.'''},
            {
                "role": "user", 
                "content": f'''Write creative Facebook ad Headlines for a given Brand and Interest Keyword.
###
Generation 1
Brand: HelloFresh is a food subscription company that sends pre-portioned ingredients to users. HelloFresh's meal kits include all the ingredients you need to cook a healthy, delicious meal. With _HelloFresh_, you can choose from a variety of recipes and meals, and the company delivers them to you 
Interest Keyword: <<Vegan Meal Kits>>
Write 3 Headlines. Each Headline must be less than 8 words.
Headline 1: Yummy <<Vegan Meal Kits>> From HelloFresh
Headline 2: Order Easy-To-Cook <<Vegan Meal Kits>>
Headline 3: Get Healthy With <<Vegan Meal Kits>>
###
Generation 2
Brand: HDFC Bank, India's leading private sector bank, offers Online NetBanking Services & Personal Banking Services like Accounts & Deposits, Cards, Loans.
Interest Keyword: <<Credit Card>>
Write 5 Headlines. Each Headline must be less than 8 words.
Headline 1: <<Credit Card>> With Easy EMIs At HDFC Bank
Headline 2: Low Interest Rates On <<Credit Cards>>
Headline 3: Maximize Your <<Credit Card>> Benefits
Headline 4: Get A <<Credit Card>> With HDFC Bank 
Headline 5: <<Credit Card>> Offers From HDFC Bank
###
Generation 3
Brand: Allbirds sells footwear and apparel. They crafted a revolutionary wool fabric made specifically for footwear. Products include Shoes, Apparel, Accessories.
Interest Keyword: <<Shoes>>
Write 5 Headlines. Each Headline must be less than 8 words.
Headline 1: Sustainable & Stylish <<Shoes> At AllBirds
Headline 2: World's Most Comfortable <<Shoes>>
Headline 3: <<Shoes>> For Any Occassion
Headline 4: Durable <<Shoes>> For an Active Lifestyle
Headline 5: Allbirds Has The Perfect <<Shoes>> For You
###
Generation 4
Brand: {self.input_dict['bu_detail']}
Interest Keyword: <<{self.input_dict['interest_keyword']}>>
Write 7 Headlines. Each Headline must be less than 8 words.
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
        return

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation_list = generation.split('\n')
            for i in range(len(generation_list)):
                generation_list[i] = generation_list[i].replace('Headline ' + str(i+1) + ':', '')
            self.extracted_generations += generation_list
        return

    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=False)
        self.post_process_list = []
        for generation in self.extracted_generations:
            self.post_process_list.append(post_process_obj.run(generation, self.input_dict))
        return 
    
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
            # n_gen is the value that core sends to us referring to how many outputs they want to be displayed
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
            "reference_headline": "Cars at best price",
            "reference_description": "Invest in cars to get better future",
            "reference_primary_text": "Invest in cars to get better future",
            "n_generations": 5
            }
    gens, logs = HeadlineInterest().run(id)
    print([gen['text'] for gen in gens])
