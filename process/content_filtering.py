import openai
from functools import wraps
import json


from ds.gpt3_key_manager import get_gpt3_key

openai.api_key, openai.organization = get_gpt3_key()


def get_content_filter_label(content_to_classify, user_id):
  #print(content_to_classify)
  user=user_id
#   print('~ calling openai content-filtering')
  response = openai.Completion.create(
      engine="content-filter-alpha",
      prompt = "<|endoftext|>"+content_to_classify+"\n--\nLabel:",
      temperature=0,
      max_tokens=1,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
      logprobs=10,
      user=user_id
      )
  output_label = response["choices"][0]["text"]
  #output_label = response["choices"][0]["text"]
  # This is the probability at which we evaluate that a "2" is likely real
  # vs. should be discarded as a false positive
  #toxic_threshold = -0.355
  #print(response)
  toxic_threshold = -0.355
  if output_label == "2":
    # If the model returns "2", return its confidence in 2 or other output-labels
    logprobs = response["choices"][0]["logprobs"]["top_logprobs"][0]
    # If the model is not sufficiently confident in "2",
    # choose the most probable of "0" or "1"
    # Guaranteed to have a confidence for 2 since this was the selected token.
    if logprobs["2"] < toxic_threshold:
        logprob_0 = logprobs.get("0", None)
        # print(logprob_0)
        logprob_1 = logprobs.get("1", None)
        # If both "0" and "1" have probabilities, set the output label
        # to whichever is most probable
        if logprob_0 is not None and logprob_1 is not None:
            if logprob_0 >= logprob_1:
                output_label = "0"
            else:
                output_label = "1"
        # If only one of them is found, set output label to that one
        elif logprob_0 is not None:
            output_label = "0"
        elif logprob_1 is not None:
            output_label = "1"
    if output_label not in ["0", "1", "2"]:
        output_label = "2"
      # If neither "0" or "1" are available, stick with "2"
      # by leaving output_label unchanged.
      # if the most probable token is none of "0", "1", or "2"
      # this should be set as unsafe
  return output_label


def content_fiter_gpt3(gpt3_outputs, user_id):
  # conbime all n_gpt3 generations to save time
  content_to_classify = '. '.join(gpt3_outputs)

  # if prompt > 2048 it cannot classify at once,
  # so divide into multiple requests

  ctc_len = len(content_to_classify)
  max_req_len = int(2048*2.8)

  for split_idx in range(0, ctc_len, max_req_len):
    # print(f'\n----------------\ncontent_to_classify : {split_idx} {split_idx+max_req_len} {ctc_len}\n', content_to_classify)
    ctc = content_to_classify[int(split_idx) : int(split_idx+max_req_len)]
    output_label = get_content_filter_label(ctc, user_id)
    if output_label == '2':
        break

  #print(content_to_classify)
  # for i in gpt3_output:
  #   gpt3_outputs=gpt3_outputs+ i+ ". "
  #   output_label = get_content_filter_label(content_to_classify, user_id)

  if output_label == "2":
    outputs = []
    #print("found unwanted content")
    for i in gpt3_outputs:
      output_label = get_content_filter_label(i, user_id)
      if output_label != "2":
          outputs.append(i)
    return outputs
    # if len(outputs) < 1:
    #   return "change your input"
    # else:
  else:
    return gpt3_outputs


def content_filter_gpt3_generations(generation_list:list, user:str):
    
    if not generation_list:
      return generation_list
    
    ### safety check on generations
    safe_generations = content_fiter_gpt3(generation_list, user)
    
    if not safe_generations:
        raise Exception('Unsafe content is detected in GPT-3 generations. Please check inputs and remove any NSFW content. If your brand requires NSFW terms kindly contact Pixis support for help.')
    else:
        print('Generations are safe for publishing')
        return safe_generations


def content_filter_input_data(input_list:list, user:str):
    ### safety check on inputs
    content_to_classify = '. '.join(input_list)

    output_label = get_content_filter_label(content_to_classify, user)
    
    if output_label == '2':
        raise Exception('Unsafe content is probably passed to GPT-3 as input. Please check inputs and remove any NSFW content. If your brand requires NSFW terms kindly contact Pixis support for help.')
    else:
        print('Inputs safe for generation')


def content_filter_inputs_outputs(func):
    '''Decorator to be used on AnyLever.run()'''
    @wraps(func)
    def inner1(*args, **kwargs):

        input_str = json.dumps(kwargs)
        # print('content_filter inputs>', input_str)
        content_filter_input_data(input_str, 'content_filter')

        result, rejected = func(*args, **kwargs)

        # extract all generations from result list/dict
        
        if type(result) == type(['list']) and all(type(el) == type('str') for el in result):
            all_gens = []
            all_gens = result
            # print('content_filter outputs>', all_gens)
            safe_generations = content_filter_gpt3_generations(all_gens, 'content_filter')

            return safe_generations, rejected
            # if result is list of str generations return all safe generations
            # from list of generations

        elif type(result) == type({'key': 'value'}) and type(result[list(result.keys())[0]]) == type(['list']):
            
            lever_type = list(result.keys())[0]
            all_gens = [perf_dict['text'] for perf_dict in result[lever_type]]
            safe_generations = content_filter_gpt3_generations(all_gens, 'content_filter')

            final_all_gens = [perf_dict for perf_dict in result[lever_type] if perf_dict['text'] in safe_generations]
            return {lever_type: final_all_gens}, rejected
            
        elif type(result) == type({'key': 'val'}):
            safe_results = {}

            for key, value in result.items():
                if type(value) == type(['list']) and all(type(el) == type('str') for el in value):
                    all_gens = []
                    all_gens = value
                    # print('content_filter outputs>', key, all_gens)
                    safe_generations = content_filter_gpt3_generations(all_gens, 'content_filter')

                    safe_results[key] = safe_generations

                else:
                    raise Exception('content_filter does not support this generation datatype.')
            
            return safe_results, rejected
        
        else:
            raise Exception('content_filter does not support this generation datatype.')


    return inner1
