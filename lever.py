import datetime
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

from abc import ABC, abstractmethod
from ds.gpt3_utils import Gpt3Generator
from ds.chatgpt_utils import ChatGptGenerator
from ds.process.postprocess import PostProcess
from ds.process.filter import FilterGenerations
from ds.process.cluster_text import ClusterText
from ds.performance.score_performance import ScorePerformance


class Lever(ABC):
    def __init__(self) -> None:
        self.min_length = 15
        self.gpt3_generator = Gpt3Generator()
        self.chatgpt_generator = ChatGptGenerator()
        self.postprocess_class = PostProcess
        self.filter_generations_class = FilterGenerations
        self.cluster_text_class = ClusterText
        self.score_performance_class = ScorePerformance
        ## Logging parameters Initialisation
        self.input_dict = {}
        self.nlg_parameters = {}
        self.prompt = ''
        self.nlg_response = {}
        self.nlg_generations_list = []
        self.extracted_generations = []
        self.post_process_list = []
        self.filtered_list = []
        self.log_json = {}
        self.log_json['time_analysis'] = {}


    def log_generate(generate):
        def wrapper_function(self, *args, **kwargs):
            start_time = datetime.datetime.now()
            generate(self, *args, **kwargs)
            time_taken = (datetime.datetime.now() - start_time).total_seconds()
            self.log_json['time_analysis']['generate'] = time_taken
            self.log_json['input_dict'] = self.input_dict
            self.log_json['prompt'] = self.prompt
            self.log_json['response'] = self.nlg_response
            self.log_json['response_text'] = self.nlg_generations_list
            logging.debug(f"{self.__class__.__name__} Lever generation  took {time_taken:.2f}secs")
        return wrapper_function

    @abstractmethod
    def generate(self) -> None:
        pass

    def log_extract_label(extract_label):
        def wrapper_function(self, *args, **kwargs):
            start_time = datetime.datetime.now()
            extract_label(self, *args, **kwargs)
            time_taken = (datetime.datetime.now() - start_time).total_seconds()
            self.log_json['time_analysis']['extract'] = time_taken
            self.log_json['extracted_labels'] = self.extracted_generations
            logging.debug(f"{self.__class__.__name__} Lever Label Extraction  took {time_taken:.2f}secs")
        return wrapper_function

    @abstractmethod
    def extract_label(self) -> None:
        pass

    def log_postprocess(postprocess):
        def wrapper_function(self, *args, **kwargs):
            start_time = datetime.datetime.now()
            postprocess(self, *args, **kwargs)
            time_taken = (datetime.datetime.now() - start_time).total_seconds()
            self.log_json['time_analysis']['postprocess'] = time_taken
            self.log_json['postprocess_labels'] = self.post_process_list
            logging.debug(f"{self.__class__.__name__} Lever Postprocessing took {time_taken:.2f}secs")
        return wrapper_function

    @abstractmethod
    def postprocess(self) -> None:
        pass

    def log_filter_generations(filter_generations):
        def wrapper_function(self, *args, **kwargs):
            start_time = datetime.datetime.now()
            filter_generations(self, *args, **kwargs)
            time_taken = (datetime.datetime.now() - start_time).total_seconds()
            self.log_json['time_analysis']['filter'] = time_taken
            self.log_json['filtered_generations'] = self.filtered_list
            logging.debug(f"{self.__class__.__name__} Lever Filter Generations took {time_taken:.2f}secs")
        return wrapper_function

    @abstractmethod
    def filter_generations(self) -> None:
        pass

    def log_run(run):
        def wrapper_function(self, *args, **kwargs):
            start_time = datetime.datetime.now()
            output, log_json = run(self, *args, **kwargs)
            time_taken = (datetime.datetime.now() - start_time).total_seconds()
            self.log_json['time_analysis']['total_time_taken'] = time_taken
            logging.debug(f"{self.__class__.__name__} Lever Took {time_taken:.2f} secs for completion")
            return output, log_json
        return wrapper_function
    
    @abstractmethod
    def run(self) -> None:
        pass
    
if __name__ == '__main__':
    pass