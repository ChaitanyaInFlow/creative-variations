import sys
import traceback

from ds.lever import Lever

class DescriptionInterest(Lever):
    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
            {
                "role": "system", 
                "content": '''You are a helpful digital marketing assistant for writing creative Facebook ad Descriptions for a given Brand and Interest Keyword.

Each Description must contain the Interest Keyword.'''},

            {
                "role": "user", 
                "content": f'''###
Generation 1
Brand: HelloFresh is a food subscription company that sends pre-portioned ingredients to users. HelloFresh's meal kits include all the ingredients you need to cook a healthy, delicious meal. With _HelloFresh_, you can choose from a variety of recipes and meals, and the company delivers them to you 
Interest Keyword: <<Vegan Meal Kits>>
Write 3 Descriptions. Each Description must be less than 8 words.
Description 1: Yummy <<Vegan Meal Kits>> from HelloFresh
Description 2: Order easy-to-cook <<Vegan Meal Kits>>
Description 3: Get Healthy With <<Vegan Meal Kits>>
###
Generation 2
Brand: Livspace is an interior design startup that offers a platform that connects people to designers, services, and products. With a variety of interior designs to choose from, _Livspace_ makes it easy for customers to get the exact look they want for their homes.
Interest Keyword: <<Home Interior>>
Write 4 Descriptions. Each Description must be less than 8 words.
Description 1: Custom <<Home Interior>> Designs at LiveSpace
Description 2: <<Home Interior>> That Reflects You
Description 3: Create Your Dream <<Home Interior>>
Description 4: <<Home Interior>> to Suit Your Taste
###
Generation 3
Brand: HDFC Bank, India's leading private sector bank, offers Online NetBanking Services & Personal Banking Services like Accounts & Deposits, Cards, Loans.
Interest Keyword: <<Credit Card>>
Write 5 Descriptions. Each Description must be less than 8 words.
Description 1: <<Credit Card>> with Easy EMIs at HDFC Bank
Description 2: Low Interest Rates on <<Credit Cards>>
Description 3: Maximize Your <<Credit Card>> Benefits
Description 4: Get a <<Credit Card>> With HDFC Bank 
Description 5: <<Credit Card>> Offers From HDFC Bank
###
Generation 6
Brand: {self.input_dict.get('bu_detail')}
Interest Keyword: <<{self.input_dict.get('interest_keyword')}>>
Write 7 Descriptions. Each Description must be less than 8 words.
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
        print("#"*50)
        print(self.prompt)

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
        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filtered_list)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)
        return
    
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
            _, _, exc_traceback = sys.exc_debug()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "debug": self.log_json}
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
    gens, logs = DescriptionInterest().run(id)
    print(gens)
    print(logs)
