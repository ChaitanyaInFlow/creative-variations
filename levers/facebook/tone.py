import sys
import traceback

from ds.lever import Lever
class TonePrimaryText(Lever):

    @Lever.log_generate
    def generate(self) -> None: 
        self.prompt = [
            {
                "role": "system", 
                "content": "You are a helpful digital marketing assistant for writing creative Facebook ad Headlines for the given Brand Info, Reference Primary Text and Tone"},
            {
                "role": "user", 
                "content": f'''Write creative Facebook ad Primary Text for the given Brand Info, Reference Primary Text and Tone.
###
Example 1
Brand Info: Swiggy is an online food ordering and delivery platform. It helps users order food from their favorite restaurants near them and track their delivery partner.
Reference Primary Text: Get match ready with Swiggy Matchday Mania! Enjoy 50% Off + free delivery on your first order.
Tone: Attention Seeking
Write 4 Variations of the Reference Primary Text for the given Brand Info and Tone. All Variations must be less than 125 characters.
Variation 1: Momos or Pizza, what's your favourite match day snack? Get 50% Off and free delivery on your first order on Swiggy today. Order now!
Variation 2: Can't miss the match for a bite? No problem! With Swiggy Matchday Mania, get 50% Off + free delivery on your first order. 
Variation 3: Cheering for your team = worked up an appetite? Swiggy has you covered! Get 50% Off + free delivery on your first order.
Variation 4: Food cravings during the game? Swiggy it! Enjoy 50% Off on your first order with Swiggy Matchday Mania.
###
Example 2
Brand Info: At HomeLane, brings together functionality and aesthetics to provide homeowners with customised and efficient home designs. Our designers specialise in home interior designs and home décor.
Reference Primary Text: Looking for home interiors? Choose India's preferred home interiors brand. With HomeLane, you can bring your dream home interiors to life in just 45 days. Speak to our Design Experts and make your house a home. Interested? Start your design journey online, from the comfort of your home.
Tone: Empathetic
Write 4 Variations of the Reference Primary Text for the given Brand Info and Tone. All Variations must be less than 125 characters.
Variation 1: Your home is your sanctuary, and we understand that. With HomeLane's customised home designs, redo your home interiors in just 45 days.
Variation 2: "A house is made of bricks and beams. A home is made of hopes and dreams." At HomeLane, we make your dreams a reality. 
Variation 3: Home is where the heart is. At HomeLane, our experts help you design a home that reflects your heart in just 45 days.
Variation 4: Every home tells a story. At Homelane, our designers can help you tell yours. Get your dream home interiors in just 45 days.
###
Example 3
Brand Info: HelloFresh is a food subscription company that sends pre-portioned ingredients to users. HelloFresh's meal kits include all the ingredients you need to cook a healthy, delicious meal. With HelloFresh, you can choose from a variety of recipes and meals, and the company delivers them to you 
Reference Primary Text: Stuck on what to have for dinner? Say hello to tasty dishes and farm-fresh ingredients, delivered right to your door!
Tone: Professional
Write 4 Variations of the Reference Primary Text for the given Brand Info and Tone. All Variations must be less than 125 characters.
Variation 1: What to cook for dinner? Let HelloFresh help you decide. Subscribe to our meal kits with pre-protioned ingredients, and recipes delivered straight to your door. 
Variation 2: No time to shop, chop or cook? Subscribe to Hellofresh's delicious and healthy ready to cook pre-portioned meal kits. 
Variation 3: Skip the grocery store and get everything you need for a delicious, home-cooked meal with HelloFresh meal kits. Subscribe now!
Variation 4: Dinner time decision making made easy with HelloFresh. Get farm-fresh ingredients and recipes delivered to your door. Subscribe today!
###
Example 4
Brand Info: {self.input_dict['bu_detail']}
Reference Primary Text: {self.input_dict['reference_primary_text']}
Tone: {self.input_dict['tone']}
Write 4 Variations of the Reference Primary Text for the given Brand Info and Tone. All Variations must be less than 125 characters.
Variation 1:'''
        }]

        self.nlg_parameters = {
            'n': 3,
            'response_length': 400,
            'temperature': 0.8,
            'top_p': 1,
            'frequency_penalty': 1,
            'presence_penalty': 1,
            'stop_seq' : [],
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
        post_process_obj = self.postprocess_class(title_case=False, exclude_exclamation=False)
        self.post_process_list = []
        for generation in self.extracted_generations:
            self.post_process_list.append(post_process_obj.run(generation, self.input_dict))
        self.log_json['post_process_list'] = self.post_process_list

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(
            max_length=125, 
            min_length=50, 
            threshold=84)
        self.filtered_list, self.log_json['discard_filter_generations'] = filter_obj.run(
            self.post_process_list, 
            reference_ad = self.input_dict['reference_primary_text'],
            input_dict=self.input_dict)
        self.log_json['filtered_generations'] = self.filtered_list
        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filtered_list)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] =  cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)
    
    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()
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
            "reference_primary_text": "Dapat bayaran dalam 24 jam",
            "tone": "happy",
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
            "tone": "happy",
            "reference_description": "You'll wear these daily!",
            "reference_primary_text": "You'll wear these daily.",
            "additional_reference": "You'll wear these daily!You'll wear these daily.",
            "language": "English"
                    }
    gens, logs = TonePrimaryText().run(id)
    print(gens)
