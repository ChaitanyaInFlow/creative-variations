import math
import sys
import traceback

from ds.lever import Lever


import logging

class HeadlineInterestKeyword(Lever):
    
    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
            {
                "role": "user", 
                "content": f'''Rephrase the given Reference Copy to generate creative Google ad Headlines for the given Brand, Reference Copy, and Interest Keyword.
#
Example 1

Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
Reference Copy: Insurance for business. On-demand liability insurance. 100% Online, In Minutes.
Interest Keyword: "insurance against cyber crime"
#
Write 6 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
#
1: On-demand "Cyber Insurance"
2: Worried about "Cyber" attacks?
3: Fast & Paperless "IT" Insurance
4: Buy "Cyber" Insurance in a Blink
5: "Cyber" Insurance, on your terms
6: Protection from "Cyber" Liability

###
Example 2

Brand: HelloFresh is a food subscription company that sends pre-portioned ingredients to users" doorstep each week. It enables anyone to cook. Quick and healthy meals designed by nutritionists and chefs. Enjoy wholesome home-cooked meals with no planning.
Reference Copy: Get Fresher, Faster Meals. Order today. Get 14 Free Meals.
Interest: "Vegan Meal, easy preparation"
#
Write 6 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
#
1: Craving Tasty "Vegan Meals"?
2: Choose Fresh "Vegan Meals"
3: Delight in Delicious "Vegan Meals"
4: Taste Terrific "Vegan Meals"
5: 14 Free Nutritious "Vegan Meals"
6: Yummy "Vegan" for Happy Heart

###
Example 3

Brand: {self.input_dict['bu_detail']}
Reference Copy: {self.input_dict['reference_headline']}
Interest: "{self.input_dict['interest_keyword']}"
#
Write 5 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
#
1:'''
            }]

        self.nlg_parameters = {
            'n' : 3,
            'response_length': 256,
            'temperature': 0.7,
            'top_p': 1,
            'frequency_penalty': 0.5,
            'presence_penalty': 2
        }
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)



    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations_list = [] 
        for generation in self.nlg_generations_list:
            generation = 'Questions:' + generation
            t_gens = generation.split('\n')
            t_gens = [':'.join(el.split(':')[1:]).strip() for el in t_gens]
            self.extracted_generations_list.extend(t_gens)


    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=True, ending_exclusions='.!', exclude_domain=True, exclude_phone_number=True)
        # TODO: + pass inputs to self.postprocess_class
        #       + article fix
        #       + incorrect offer
        #       + preserve unusual capitalization from inputs

        self.post_process_list = []
        for generation in self.extracted_generations_list:
            self.post_process_list.append(post_process_obj.run(generation, input_dict=self.input_dict))
        self.log_json['self.postprocess_class_labels'] = self.post_process_list


    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_pipeline_obj = self.filter_generations_class(
            min_length=self.min_length, 
            max_length=30, 
            filter_phrase=self.input_dict['interest_keyword'])
        # TODO: Add ISF filter
        self.filter_generations_list, self.filtered_generations = filter_pipeline_obj.run(
            generations_list=self.post_process_list, 
            reference_ad=self.input_dict['reference_headline'],
            input_dict=self.input_dict)
        self.log_json['filtered_generations'] = self.filter_generations_list

        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filter_generations_list)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)


    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict

            no_of_outputs = self.input_dict['n_generations']
            self.input_dict['n_generations'] *= 0.1
            self.input_dict['n_generations'] = math.ceil(self.input_dict['n_generations']) + 3

            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()

            self.filter_generations_list = {
                'interest': self.performance_generations_dict_list[:no_of_outputs]
            }

            return self.filter_generations_list, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return {"interest":[]}, updated_log_json 

if __name__ == '__main__':
    # TODO: add prompt temptlate, params, support dict to csv for google

    pt= '''Rephrase the given Reference Copy to generate creative Google ad Headlines for the given Brand, Reference Copy, and Interest Keyword.
#
Example 1

Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
Reference Copy: Insurance for business. On-demand liability insurance. 100% Online, In Minutes.
Interest Keyword: "cyber insurance for business"
#
Write 6 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
#
1: On-demand "Cyber Insurance"
2: Worried about "Cyber" attacks?
3: Fast & Paperless "IT" Insurance
4: Buy "Cyber" Insurance in a Blink
5: "Cyber" Insurance, on your terms
6: Protection from "Cyber" Liability
###
Example 2

Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
Reference Copy: Modern Home Interior Designs. Unbeatable Quality & 23% Off. Customize your Dream Home
Interest Keyword: "Modular Kitchen"
#
Write 6 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
#
1: Get 23% off on "Modular Kitchen"
2: The "Kitchen" of Your Dreams
3: Compact "Kitchen" Interiors
4: 1000s of "Modular Kitchen" Ideas
5: Eying for "Modular Style Kitchen"?
6: "Modular Kitchen" on Your Budget
###
Example 3

Brand: HelloFresh is a food subscription company that sends pre-portioned ingredients to users" doorstep each week. It enables anyone to cook. Quick and healthy meals designed by nutritionists and chefs. Enjoy wholesome home-cooked meals with no planning.
Reference Copy: Get Fresher, Faster Meals. Order today. Get 14 Free Meals.
Interest: "Vegan Meal, easy preparation"
#
Write 6 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
#
1: Craving Tasty "Vegan Meals"?
2: Choose Fresh "Vegan Meals"
3: Delight in Delicious "Vegan Meals"
4: Taste Terrific "Vegan Meals"
5: 14 Free Nutritious "Vegan Meals"
6: Yummy "Vegan" for Happy Heart

###
Example 4

Brand: {self.input_dict['bu_detail']}
Reference Copy: {reference_headline}
Interest Keyword: "{self.input_dict['interest_keyword']}"
#
Write 5 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
#
1:'''


    pp = {
        'engine': 'text-davinci-002',
        'response_length': 100,
        'temperature': 0.85,
        'top_p': 1,
        'frequency_penalty': 0.4,
        'presence_penalty': 0,
        'stop_seq' : ["###"]
    }
    sd = {}

    id = {
        "bu_detail": "SwiGGy delivers yummy food to your doorsteps.",
        "reference_headline": "Get tasty food at best prices. Delivered in 20 mins. Choose from 500+ restaurants. $20 Off",
        "interest_keyword": "Pizza",
        "bu_name": "Swiggy",
        "benefit_used": "Gluten free",
        "n_generations": 10
    }

    # headline_gen_obj = HeadlineInterest()
    # gens, rej_gens = headline_gen_obj.run(input_dict=id)
    # print(gens)
    # print(len(gens['interest']))