import random
from typing import List, Dict
from ds.process.cluster_text import ClusterText
import itertools



class Bundle:
    def __init__(self, description_discard_ratio: int = .2,
                 primary_text_discard_ratio: int = .3
                 ) -> None:
        self.description_discard_ratio = description_discard_ratio
        self.primary_text_discard_ratio = primary_text_discard_ratio

    def get_bundles(self, 
                    headline_list: List[Dict], 
                    description_list: List[Dict], 
                    primary_text_list: List[Dict], 
                    stories: None, 
                    image_text_list: List = [], 
                    input_dict: Dict = {}) -> List[str]:
        cluster_text_obj = ClusterText()

        headline_description_bundle_list = []

        if len(headline_list) == 0 and len(description_list) == 0 and len(primary_text_list) != 0:
            for pt in primary_text_list:
                headline_description_bundle_list.append({
                    'headline': '',
                    'description': ''
                })

        if len(headline_list) == 0:
            if description_list:
                for description in description_list:
                    headline_description_bundle_list.append({
                        'headline': '',
                        'description': description
                    })

        elif len(description_list) == 0:
            for headline in headline_list:
                headline_description_bundle_list.append({
                    'headline': headline,
                    'description': ''
                })
        else:
            for headline in headline_list:
                if description_list:
                    description_list = cluster_text_obj.get_matches_sorted(
                        ref_ad=headline,
                        generations_list=description_list,
                        discard_ratio=self.description_discard_ratio,
                        generation_type='')
                    if description_list:
                        print("#####",description_list)

                        headline_description_bundle_list.append({
                            'headline': headline,
                            'description': description_list.pop(0)
                        })
                        print("#####",description_list)

        
        ref_primary_text = {"text" : input_dict['reference_primary_text'] +
            ' ' + input_dict['bu_detail']}
        sorted_primary_text_list = cluster_text_obj.get_matches_sorted(
            ref_ad=ref_primary_text,
            generations_list=primary_text_list,
            discard_ratio=self.primary_text_discard_ratio,
            generation_type='')


        bundle_output_list = []
        if image_text_list:
            for headline_description_dict, primary_text, image_text in zip(headline_description_bundle_list, sorted_primary_text_list, image_text_list):
                image = []
                image_dict = {'layer_name': "layer_1",
                                'layer_text': image_text}
                image.append(image_dict)
                bundle_output_list.append({
                    'primary_text': primary_text,
                    'image': image,
                    **headline_description_dict
                })
        print("stories", stories)
        if stories:
            media_type = input_dict.get('media_type', None)
            if media_type is None:
                raise Exception(
                    "Media Type is not specified, Please specify the media type. Supported media types are image/video")
            return self.story_bundling(headline_description_bundle_list, sorted_primary_text_list, stories, bundle_output_list, media_type=media_type)
        else:
            if sorted_primary_text_list:
                for headline_description_dict, primary_text in zip(headline_description_bundle_list, sorted_primary_text_list):
                    bundle_output_list.append({
                        'primary_text': primary_text,
                        **headline_description_dict
                    })
            else:
                for headline_description_dict in headline_description_bundle_list:
                    bundle_output_list.append({
                        'primary_text': '',
                        **headline_description_dict
                    })
            return bundle_output_list

    def story_bundling(self, headline_description_bundle_list, sorted_primary_text_list, stories, bundle_output_list, media_type=None):
        # import pdb; pdb.set_trace
        if len(stories) < len(headline_description_bundle_list):
            stories = random.choices(stories, k=len(
                headline_description_bundle_list))

        if sorted_primary_text_list: 

            for headline_description_dict, primary_text, story in zip(headline_description_bundle_list, sorted_primary_text_list, stories):
                bundle_output_list.append({
                    'primary_text': primary_text,
                    media_type: story,
                    **headline_description_dict
                })
        else:
            for headline_description_dict, story in zip(headline_description_bundle_list, stories):
                bundle_output_list.append({
                    'primary_text': '',
                    media_type: story,
                    **headline_description_dict
                })
        return bundle_output_list


def bundle_v5(headline_generations, description_generations, primary_text_generations, stories: None, input_dict):

    bundle_list = Bundle().get_bundles(
        headline_list= headline_generations,
        description_list= description_generations,
        primary_text_list= primary_text_generations,
        stories= stories,
        input_dict=input_dict

    )
    print("###########", len(bundle_list))

    return bundle_list


if __name__ == '__main__':

    stories =  [
    [
      {
        "layer_name": "Text 1",
        "layer_text": "Make Mealtime A Breeze "
      },
      {
        "layer_name": "Text 2",
        "layer_text": " With HelloFresh"
      }
    ],
    [
      {
        "layer_name": "Text 1",
        "layer_text": "We Do The Meal Planning "
      },
      {
        "layer_name": "Text 2",
        "layer_text": " So You Don't Have To"
      }
    ],
    [
      {
        "layer_name": "Text 1",
        "layer_text": "New Recipes Every Week "
      },
      {
        "layer_name": "Text 2",
        "layer_text": " With HelloFresh"
      }
    ],
    [
      {
        "layer_name": "Text 1",
        "layer_text": "Low Prep, Easy Cleanup "
      },
      {
        "layer_name": "Text 2",
        "layer_text": " With HelloFresh"
      }
    ]
  ]
    headline_generations =  [
    {
      "text": "Low Prep, Easy Cleanup Options",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 9.8,
      "readability_score": 83,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9792367054942609
    },
    {
      "text": "140+ Menu Items On Offer",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 9.8,
      "readability_score": 83,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9792367054942609
    },
    {
      "text": "Free Meal On Sign Up With HelloFresh",
      "offer_label": False,
      "benefit_label": False,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 9.7,
      "readability_score": 95,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9679630686165213
    },
    {
      "text": "140+ Menu Items For Your Enjoyment",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": True,
      "performance_score": 8.8,
      "readability_score": 75,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8844441808191807
    },
    {
      "text": "Only $4.99/Meal With HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 77,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8328817430501492
    },
    {
      "text": "140+ Menu Items From HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 97,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8271350000747908
    },
    {
      "text": "Quick & Easy Meals From HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 97,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8271350000747908
    },
    {
      "text": "Try HelloFresh & Get $4.99/Meal",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 97,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8271350000747908
    },
    {
      "text": "Ready To Eat Oven Meals Now Available",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 8.2,
      "readability_score": 88,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8194558990008554
    },
    {
      "text": "Oven Ready Meals Delivered",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 8.1,
      "readability_score": 63,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8118570475758757
    },
    {
      "text": "Calorie & Carb Smart Options",
      "offer_label": False,
      "benefit_label": False,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 7.1,
      "readability_score": 63,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.713568377337397
    },
    {
      "text": "Try Delicious Meals With HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 7,
      "readability_score": 69,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7043360902820472
    }
  ]
    description_generations =  [
    {
      "text": "Low Prep, Easy Cleanup Options",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 9.8,
      "readability_score": 83,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9792367054942609
    },
    {
      "text": "Try HelloFresh Today",
      "offer_label": False,
      "benefit_label": False,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.8,
      "readability_score": 77,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8750622391665488
    },
    {
      "text": "140+ Menu Items From HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 97,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8271350000747908
    },
    {
      "text": "140+ Menu Items - Limited Time Only",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 61,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8269024066838818
    },
    {
      "text": "Get A Free Meal With HelloFresh",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8,
      "readability_score": 96,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8011550376757937
    },
    {
      "text": "Get A Free HelloFresh Meal Today",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 7.6,
      "readability_score": 82,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7562658859489523
    },
    {
      "text": "Only $4.99/Meal - Limited Time Offer",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 7.5,
      "readability_score": 41,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7517623222227745
    },
    {
      "text": "Carb & Calorie Smart Options",
      "offer_label": False,
      "benefit_label": False,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 7.1,
      "readability_score": 63,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.713568377337397
    },
    {
      "text": "Try America's #1 Meal Kit Now",
      "offer_label": False,
      "benefit_label": False,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 7,
      "readability_score": 61,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7037606131113024
    },
    {
      "text": "$4.99/Meal - Don't Miss Out",
      "offer_label": False,
      "benefit_label": False,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 7,
      "readability_score": 97,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7004349501971271
    },
    {
      "text": "$4.99/Meal - 140+ Menu Items",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 6.5,
      "readability_score": 97,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.6522862585430887
    },
    {
      "text": "20-Min Meals Ready To Eat",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 6.5,
      "readability_score": 97,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.6522862585430887
    }
  ]
    primary_text_generations =  [
    {
      "text": "Get creative in the kitchen with HelloFresh - America's #1 Meal Kit. Plus, try us out for free! 😋\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.5,
      "readability_score": 80,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8520477744777369
    },
    {
      "text": "Try the most popular Meal Kit today - HelloFresh! Sign up Now for a free meal.\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.1,
      "readability_score": 81,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8145242776547121
    },
    {
      "text": "Fresh ingredients delivered right to you - try HelloFresh & get a free meal when you sign up!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": True,
      "performance_score": 7.7,
      "readability_score": 67,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7738445165945166
    },
    {
      "text": "Get creative in the kitchen without any of the hassle - try America's #1 Meal Kit today + get $4.99 off!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 7,
      "readability_score": 57,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7008519757664671
    },
    {
      "text": "Cooking made easy with pre-portioned ingredients from HelloFresh - America's #1 Meal Kit. Try it Now and get a free meal!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 6.3,
      "readability_score": 58,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.6329697715061513
    },
    {
      "text": "Experience the convenience of having fresh ingredients delivered to your door with HelloFresh. Try it Now!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": True,
      "performance_score": 5.7,
      "readability_score": 45,
      "performance_labels": "Medium Performance",
      "performance_probabilities": 0.5717476439423528
    },
    {
      "text": "Enjoy fresh ingredients & delicious recipes with HelloFresh and get a free dinner on us!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 5.6,
      "readability_score": 54,
      "performance_labels": "Medium Performance",
      "performance_probabilities": 0.5577411707381783
    },
    {
      "text": "Choose from a variety of recipes & have them delivered to your door with HelloFresh. Limited time Only offer - try us for free!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 5,
      "readability_score": 64,
      "performance_labels": "Medium Performance",
      "performance_probabilities": 0.5015692181232692
    },
    {
      "text": "Make dinnertime easy with step-by-step recipes and fresh ingredients from HelloFresh. Free meal on us!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 5,
      "readability_score": 67,
      "performance_labels": "Medium Performance",
      "performance_probabilities": 0.4976775659008904
    },
    {
      "text": "Why not try out America's #1 Meal Kit? Get a free meal when you sign up for HelloFresh today!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": False,
      "brand_centric": True,
      "customer_centric": True,
      "performance_score": 3.1,
      "readability_score": 79,
      "performance_labels": "Low Performance",
      "performance_probabilities": 0.3106986106819435
    },
    {
      "text": "Ready for something new? Sign up for HelloFresh and get a free meal right away!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": False,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 1.5,
      "readability_score": 88,
      "performance_labels": "Low Performance",
      "performance_probabilities": 0.15328679653679655
    },
    {
      "text": "Get America's #1 Meal Kit delivered right to your door, plus get a free recipe when you sign up!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": False,
      "brand_centric": False,
      "customer_centric": True,
      "performance_score": 0.5,
      "readability_score": 64,
      "performance_labels": "Low Performance",
      "performance_probabilities": 0.05
    }
  ]
  
    stories = [
    [
      {
        "layer_name": "Text 1",
        "layer_text": "Meal Planning Made Easy "
      },
      {
        "layer_name": "Text 2",
        "layer_text": " With HelloFresh"
      }
    ],
    [
      {
        "layer_name": "Text 1",
        "layer_text": "Make Meal Time Easier "
      },
      {
        "layer_name": "Text 2",
        "layer_text": " With HelloFresh"
      }
    ],
    [
      {
        "layer_name": "Text 1",
        "layer_text": "We Plan Your Meals "
      },
      {
        "layer_name": "Text 2",
        "layer_text": " So You Don't Have To"
      }
    ],
    [
      {
        "layer_name": "Text 1",
        "layer_text": "Carb & Calorie Smart "
      },
      {
        "layer_name": "Text 2",
        "layer_text": " With HelloFresh"
      }
    ]
  ]
    headline_generations = [
    {
      "text": "Low Prep, Easy Cleanup Options",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 9.8,
      "readability_score": 83,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9792367054942609
    },
    {
      "text": "$4.99/Meal With HelloFresh",
      "offer_label": False,
      "benefit_label": False,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 9.5,
      "readability_score": 98,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9466032439500998
    },
    {
      "text": "140+ Menu Options From HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 9.1,
      "readability_score": 83,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9088526602094801
    },
    {
      "text": "140+ Menu Options With HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 9.1,
      "readability_score": 83,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9088526602094801
    },
    {
      "text": "Get 140+ Recipes Delivered To You",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": True,
      "performance_score": 8.8,
      "readability_score": 75,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8844441808191807
    },
    {
      "text": "Low Prep, Great Taste With HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 96,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8316211908631652
    },
    {
      "text": "Quick & Easy Meals With HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 97,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8271350000747908
    },
    {
      "text": "Low Prep, Easy Cleanup W/HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 97,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8271350000747908
    },
    {
      "text": "Try HelloFresh & Save $4.99/Meal",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 97,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8271350000747908
    },
    {
      "text": "Carb & Calorie Smart Meals With HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 82,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8256386835686459
    },
    {
      "text": "Calorie& Carb Smart Meals",
      "offer_label": False,
      "benefit_label": False,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 7,
      "readability_score": 77,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7006747359086716
    },
    {
      "text": "Quick Cleanup & Ready To Eat",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 6.5,
      "readability_score": 97,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.6522862585430887
    }
  ]
    description_generations = [
    {
      "text": "Quick & Easy - 20 Min Options",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 9.8,
      "readability_score": 83,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9792367054942609
    },
    {
      "text": "140+ Menu Items Under $4.99/Meal",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 9.8,
      "readability_score": 83,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9792367054942609
    },
    {
      "text": "20 Min. Options With HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 9.1,
      "readability_score": 83,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9088526602094801
    },
    {
      "text": "Ready-to-Eat Oven Meals From HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 9.1,
      "readability_score": 83,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9088526602094801
    },
    {
      "text": "20 Min Meals - Carb & Calorie Smart",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 8.7,
      "readability_score": 82,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8715438469896764
    },
    {
      "text": "Ready-to-Eat Meals With HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 77,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8328817430501492
    },
    {
      "text": "Low Prep, Easy Cleanup With HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 96,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8316211908631652
    },
    {
      "text": "Carb & Calorie Smart Recipes At HelloFresh",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.3,
      "readability_score": 82,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8256386835686459
    },
    {
      "text": "140+ Menu Options Available",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 8.1,
      "readability_score": 63,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8118570475758757
    },
    {
      "text": "Most Popular Meal Kit, Limited Time Only",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 7.7,
      "readability_score": 46,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7713277723527342
    },
    {
      "text": "America's Most Popular Meal Kit",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 7.5,
      "readability_score": 27,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7548907296879647
    },
    {
      "text": "Only $4.99/Meal, Limited Time",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": False,
      "customer_centric": False,
      "performance_score": 7.4,
      "readability_score": 42,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7435085947668799
    }
  ]

    primary_text_generations = [
    {
      "text": "Why choose HelloFresh? Get your first meal free when you sign up Now!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": True,
      "performance_score": 9.9,
      "readability_score": 95,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.9927160493827161
    },
    {
      "text": "HelloFresh is the most popular meal kit for a reason. Try us out Now!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.4,
      "readability_score": 81,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8398928923228546
    },
    {
      "text": "Get creative in the kitchen with step-by-step recipes from HelloFresh!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.4,
      "readability_score": 79,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.838501164956843
    },
    {
      "text": "Why choose HelloFresh as your go-to Meal Kit? Find out Now and get a free meal on us!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.2,
      "readability_score": 86,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8230488734834708
    },
    {
      "text": "Discover why so many people trust HelloFresh as their go-to meal kit. Sign up today and get a free meal.\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.2,
      "readability_score": 72,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8180921323651614
    },
    {
      "text": "Stop searching for what to have for dinner - let HelloFresh take care of it all. Sign up Now & get a free meal!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8.1,
      "readability_score": 85,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.8071541366413656
    },
    {
      "text": "Delicious recipes and fresh ingredients - why choose anyone else? Try HelloFresh today!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 8,
      "readability_score": 54,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7950501810476824
    },
    {
      "text": "Discover why so many love cooking with HelloFresh. Get a free meal when you sign up Now!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": True,
      "performance_score": 7.6,
      "readability_score": 80,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7635029317806825
    },
    {
      "text": "Enjoy delicious meals made easy with HelloFresh. Grab yours Now and get a free trial Meal Kit!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": True,
      "performance_score": 7.6,
      "readability_score": 80,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.7635029317806825
    },
    {
      "text": "Why not give it a try? With HelloFresh, you can get one free trial Meal Kit when you sign up today!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": False,
      "brand_centric": True,
      "customer_centric": True,
      "performance_score": 6.9,
      "readability_score": 85,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.6884761904761904
    },
    {
      "text": "Say hello to tasty, homemade meals without all the hassle - thanks to HelloFresh! Limited time offer.\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": False,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 6.8,
      "readability_score": 66,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.6803027265526567
    },
    {
      "text": "Experience the convenience of pre-portioned, farm-fresh ingredients from HelloFresh – try us out for free today!\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart.",
      "offer_label": True,
      "benefit_label": True,
      "brand_centric": True,
      "customer_centric": False,
      "performance_score": 6.7,
      "readability_score": 32,
      "performance_labels": "High Performance",
      "performance_probabilities": 0.6694465327747936
    }
  ]
    input_dict = { "bu_name": "HelloFresh", 
                "brand_id": "18391961-c14e-4c49-94c0-16117bbfe383", 
                "bu_detail": "HelloFresh delivers step-by-step recipes and fresh, pre-portioned ingredients right to your door. Get a free meal when you sign up for HelloFresh. Choose from a variety of recipes and have them delivered to your door.", 
                "brand_name": "HelloFresh", 
                "media_type" : 'image',
                "interest_keyword": "Offer,Free Meal,Healthy", 
                "reference_headline": "Try America's #1 Meal Kit",
                "reference_description": "Limited time only!", 
                "reference_primary_text": "Why HelloFresh is the Most Popular Meal Kit👇\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart."}

    input_dict = { "bu_name": "HelloFresh", 
                "brand_id": "18391961-c14e-4c49-94c0-16117bbfe383", 
                "bu_detail": "HelloFresh delivers step-by-step recipes and fresh, pre-portioned ingredients right to your door. Get a free meal when you sign up for HelloFresh. Choose from a variety of recipes and have them delivered to your door.", 
                "brand_name": "HelloFresh", 
                "media_type" : 'image',
                "interest_keyword": "Offer,Free Meal,Healthy", 
      "reference_headline": "Try America's #1 Meal Kit",
      "reference_description": "Limited time only!",
      "reference_primary_text": "Why HelloFresh is the Most Popular Meal Kit👇\n😍Only $4.99/Meal\n🍱Now 140+ menu items\n🥘Ready to eat oven ready meals\n✅Quick & Easy meals (20 min options)\n🧼Low prep, easy cleanup options.\n💪Carb & calorie smart."}

    bundle_v5(
        headline_generations=headline_generations,
        description_generations=description_generations,
        primary_text_generations=primary_text_generations,
        stories=stories,
        input_dict=input_dict

    )