from ds.lever import Lever


class UACExtendedThemeFromSerpGeneration(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
            {
                "role": "system", 
                "content": f'''You are an experienced marketer consulting for large brands on what Ad Campaigns to run next. You have to help these brands to come up with new Ideas in a given theme to create Ads used to retarget existing customers or target new customers. Recommend Ideas that build on top of the given theme to further enhance the Theme, or provide more context to the Theme. Top google search results for given theme is provided, you can use these to help with recommeded extended ideas.
###
Recommend Extended themes to run marketing campaigns for the given Brand, Themes.

Brand: Swiggy is an Indian online food ordering and delivery platform.
Theme: Dinner Date
Google Results:
```
- Apart from the wealth of gourmet restaurants and cafes available for delivery on the list, you also get to make pre-orders for your meals up
- The perfect date night begins with a game of Delivery Roulette ... dinner date didn't mean we couldn't make meals part of the fun
- Haar At Home offers an amazing way to enjoy Valentine's Day with a delicious, romantic fine dining meal delivered right at your
- 21 Most Romantic Restaurants in Delhi for the Perfect Dream Date ... magicpin is the best food delivery platform in India
- Whether you feel lazy to cook or have surprise guests at your place, ordering from
- With hundreds of home delivery restaurants around, life has become easier
- Now, people search for a dish and then find a restaurant
- Fast Food Delivery Services Darjeeling More , Siliguri
- Best Food Delivery in Bengaluru, Bangalore District
- 21 Best Romantic Restaurants In Delhi-Updated List
- Perfect date night idea: Play "delivery roulette"
- Date night restaurant home deliveries
- Bengaluru Delivery Restaurants
- Byg Brewski Brewing Company
- Three Squares Cafe + Bar
- Super Bowl of China
- Mexican, American
- Food & Beverages
- Time Traveller
- Nona's Kitchen
- 1,843 reviews
- Indian, Asian
- The Takeout
- Mimi & Bros
```
> Ideas from Google Results for Dinner Date:
1: Enjoy gourmet meals
2: Delivery roulette
3: Surprise plan
4: Romantic fine dining
###
Recommend Extended themes to run marketing campaigns for the given Brand, Themes.

Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
Themes: Kitchen Interior
Google Results:
```
- HomeLane is a pioneer in the kitchen interior designing world and a market leader when it comes to churning out the most memorable home interior designs
- Explore Michelle Chong's board "Kitchen Interiors", ... See more ideas about kitchen interior, kitchen inspirations, kitchen design
- Beige modular kitchen with blue peninsula Interior Design by Urban Company Professional  Design
- Explore the finest interior design ideas for your kitchen to go with the trend
- Inspiring design ideas for your modular kitchen cabinets, countertops, etc
- Here, interior designer Heidi Caillier camouflaged a bulky appliance with
- Interior design for kitchen is not just cabinets and accessories
- Take a look at some of our favorite kitchen design ideas
- 15+ Indian Kitchen Design Images from Real Homes
- Modular Kitchen Interior Design Ideas
- Modular Kitchen Designs With Prices
- Add a pop of colour & accessorise
- Kitchen Countertops Options
- 6: Shabby Chic Interior
- 7: Bohemian Interior
- Jul 28, 2022
```
> Ideas from Google Results for Kitchen Interior:
1: Modular kitchen
2: Peninsula interior
3: Camouflage bulky appliance
4: Add colour to your kitchen
5: Shabby chic interior
6: Bohemian interior 
###
Recommend Extended themes to run marketing campaigns for the given Brand, Themes.

Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
Theme: Cyber Insurance, Free consultation
Google Results:
```
- Cyber insurance protects businesses from the high costs of a data breach ... Compare free quotes and start a cyber policy today with Insureon
- Easily assess your cyber risk and get a free quote to learn which cyber insurance coverages to consider for your situation
- Cyber liability insurance protects businesses from the high costs of a data breach or malicious software attack
- Cyber insurance is one option that can help protect your business against losses resulting from a cyber attack
- Cyber liability insurance can help protect your business from data breaches and other cyberattacks
- one-on-one consultation with a cyber security expert, training tools and videos to
- Learn about cyber insurance coverage, and more from Travelers
- Cyber Insurance Consulting, Cybersecurity Insurance Services
- Cyber Liability Insurance New York, California & Washington
- Quoting this valuable coverage takes just minutes
- Learn more about cyber insurance with Paychex
- Cyber Liability Insurance for Small Business
- How much does a cyber liability policy cost
- Cyber Liability & Data Breach Insurance
- Cover for cybercrime and data breaches
- We provide Cyber Insurance Consulting
- Broad business interruption cover
- National Cyber Security Alliance
- Market-leading incident response
- Get a Cyber Liability Quote Now
- Free access to our mobile app
- Cyber Security refers to the
- Get a free quote in minutes
- Cyber Liability Insurance
- Federal Trade Commission
- Order Free Publications
- Progressive Commercial
- Business Insurance To
- Travelers Insurance
- 360 Coverage Pros
- Ransomware Cyber
- Cyber Insurance
- Underwriting
- The Security
```
> Ideas from Google Results for Cyber Insurance:
1: Protect from data breach
2: Easily assess your cyber risks
3: Compare insurance
4: Protect against malicious software attacks
5: Consultation with a cyber security expert
6: Protect from ransomware 
###
Recommend Extended themes to run marketing campaigns for the given Brand, Themes.

Brand: HelloFresh is a food subscription company that sends pre-portioned ingredients to users doorstep each week. It enables anyone to cook. Quick and healthy meals designed by nutritionists and chefs. Enjoy wholesome home-cooked meals with no planning.
Theme: Vegan Meal, easy preparation
Google Results:
```
- If you don't want ready-to-eat meals but are also looking to minimize prep time in the kitchen, consider Green Chef the Goldilocks of vegan meal
- Because all Purple Carrot meal kits and prepared meals are vegan-friendly, this service is our pick for the best overall plant-based meal
- Why It's Worth It: Green Chef makes it easy to cook colorful, flavorful meals in just 20 to 40 minutes and is
- These tasty vegan and vegetarian meal subscriptions are an easy way to cut down on meat in 2022
- Receive new plant-based recipes and pre-portioned ingredients delivered to your door each week
- Take your vegan meal plan to the next level with Green Chef & our vegan food delivery service
- Recipe instructions can be confusing with customization options
- Here are our top picks based on cost, availability, and more
- Tasty Vegan Meal Kits ✓ Flavorful Vegan Recipes ✓ Start
- 13 Best Plant-Based Meal Delivery Services of 2022
- Discover the power of a plant-based diet
- Purple Carrot Plant-Based Meal Delivery
- Best Value: Daily Harvest
- Best Organic: Green Chef
- Best Overall: Sunbasket
- This Week’s Menu
- The Spruce Eats
- Splendid Spoon
- Our Top Picks
- Daily Harvest
- Fresh N Lean
- Food & Wine
- All Recipes
```
> Ideas from Google Results for Vegan Meal:
1: Minimize preperation time
2: Cook colorful, flavorful meals
3: Cook meaks in 20-40 minutes
4: Cut down on meat
5: Pre-portioned ingredients delivered each week
###
Recommend Extended themes to run marketing campaigns for the given Brand, Themes.

Brand: Clash of Clans is a free-to-play mobile strategy video game.
Themes: Save time, fast troop training
Google Results:
```
- According to the developers, the aim of this initiative is to allow players to explore new strategies without having to break the bank if it
- In Vikings War of Clans it's entirely possible to get a training speed boost of between 500%-600% using the above tips
- For those of you that don't know, the quick train feature lets you save 3 army compositions for a “quick train”
- All troop and spell training now happens in single, dedicated tabs
- There is also an option to boost troop production for an hour
- In Clash of Clans, why does the troop capacity say your max
- 8 Tips to Train Troops Faster by Erik The Red
- Clash of Clans army training becomes free
- Clash of Clans Faster Army Training Tips
- Quick Train lets you create 3
- Top Hacks for Training Troops
- Army Training Revamp & Quick
- one button tap and whatever
- Pace the troops building
- Clash of Clans Wiki
- Marks Angry Review
- : r/ClashOfClans
- Vikings Forum
```
> Ideas from Google Results for fast troop training:
1: Allow players to explore new strategies
2: Get training speed boost
3: Save army compositions with quick train
4: Dedicated tab for troop and spell training
5: Free army training
###
Recommend Extended themes to run marketing campaigns for the given Brand, Themes.

Brand: {self.input_dict['brand_detail']}
Themes: {self.input_dict['theme']}
Google Results:
```
{self.input_dict['serp_data']}
```
> Ideas from Google Results for {self.input_dict['theme']}:
1:'''
            }]

        self.nlg_parameters = {
            'temperature': 0.75,
            'response_length': 100,
            'top_p': 1,
            'frequency_penalty': 0.8,
            'presence_penalty': 0.4,
            'n': 2,
        }        
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)
        
    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation = '1:' + generation
            t_gens = generation.split('\n')
            t_gens = [':'.join(el.split(':')[1:]).strip() for el in t_gens]
            self.extracted_generations.extend(t_gens)
       
    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=True)
        self.post_process_list = []
        for generation in self.extracted_generations:
            self.post_process_list.append(post_process_obj.run(generation))

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(
            max_length=70,
            threshold=80)
        self.filtered_list, self.discarded_list = filter_obj.run(
            self.post_process_list, reference_ad='',
            input_dict=self.input_dict)

    @Lever.log_run       
    def run(self, input_dict):
        self.input_dict = input_dict
        self.generate()
        self.extract_label()
        self.postprocess()
        self.filter_generations()

        return self.filtered_list, []
   
if __name__ == '__main__':
    pass
# ad_account_id = 2904992326
# ad_group_id = 63963090431
# generations, input_headlines, input_descriptions = generate(ad_account_id, ad_group_id)
