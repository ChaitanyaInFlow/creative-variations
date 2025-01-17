
import time
import openai
from multiprocessing.pool import ThreadPool
import pandas as pd

def generate(n):
    start_time = time.time()
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": '''Rephrase the given Reference Copy to generate creative Google ad Headlines for the given Brand, Reference Copy, and Interest Keyword.
    #
    Example 1

    Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
    Reference Copy: Insurance for business. On-demand liability insurance. 100% Online, In Minutes.
    Interest Keyword: "cyber insurance for business"
    #
    Write 6 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
    #
    1: On-Demand "Cyber Insurance"
    2: Worried About "Cyber" Attacks?
    3: Fast & Paperless "IT" Insurance
    4: Buy "Cyber" Insurance In A Blink
    5: "Cyber" Insurance, On Your Terms
    6: Protection From "Cyber" Liability
    ###
    Example 2

    Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
    Reference Copy: Modern Home Interior Designs. Unbeatable Quality & 23% Off. Customize your Dream Home
    Interest Keyword: "Modular Kitchen"
    #
    Write 6 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
    #
    1: Get 23% Off On "Modular Kitchen"
    2: The "Kitchen" Of Your Dreams
    3: Compact "Kitchen" Interiors
    4: 1000s of "Modular Kitchen" Ideas
    5: Eying for "Modular Style Kitchen"?
    6: "Modular Kitchen" On Your Budget
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
    3: Delight In Delicious "Vegan Meals"
    4: Taste Terrific "Vegan Meals"
    5: 14 Free Nutritious "Vegan Meals"
    6: Yummy "Vegan" for Happy Heart

    ###
    Example 4

    Brand: Acko is a private sector general insurance company in India. Acko provides low cost insurance with big benefits. Get paperless claims experience with every policy. Acko makes getting an insurance easy.
    Reference Copy: Trusted By 8.2 Cr* Customers. Buy Standalone OD Insurance. Save Upto 70%* On OD Insurance
    Interest Keyword: "own damage(OD)"
    #
    Write 5 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
    #
    1:'''}
        ],
        n=n
    )
    print(time.time() - start_time, "secs")
    return "||".join([choice['message']['content'].strip() for choice in response.get('choices')])

gpt3_generation_objs = []
pool = ThreadPool(processes=1000)
for i in range(1000):
    for _ in range(20):
        aync_obj = pool.apply_async(generate, args=(5,))
        gpt3_generation_objs.append(aync_obj)
    time.sleep(.1) 

result = []
for idx,gen_obj in enumerate(gpt3_generation_objs):
    try:
        result.append(gen_obj.get())
    except Exception as e:
        print(idx, str(e))
print(len(result))
pd.DataFrame(result).to_csv('results.csv',index=False)

