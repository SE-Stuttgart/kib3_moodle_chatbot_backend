from sentence_transformers import SentenceTransformer, util
import numpy
import torch
import os

class Utterance_Mapper():
    """
    Maps the utterance to another utterance which is known to the system via a neural network.
    """
    def __init__(self, embedder_model):
        """
        Initializes the Utterance_Mapper.
        """
        # set device to cuda or cpu
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model = embedder_model
        self.embedder = SentenceTransformer(embedder_model, device=self.device)
        self.threshold = 0.945
        data_dict = torch.load('embeddings.pt', map_location=self.device)

        # Retrieve the embeddings and labels from the dictionary
        self.corpus = data_dict['corpus']
        self.embeddings = data_dict['embeddings']
        self.labels = data_dict['labels']
    
    def get_most_similar(self, utterance):
        """
        Returns the most similar utterance to the given utterance.
        """
        query_embedding = self.embedder.encode(utterance, convert_to_tensor=True)
        cos_scores = util.pytorch_cos_sim(query_embedding, self.embeddings)[0]
        top_results = torch.topk(cos_scores, k=1)
        mapped_utterance = self.corpus[top_results[1]]
        print( "Query: {}, Mapped utterance: {}, label: {}, score: {}   ".format(utterance, mapped_utterance, self.labels[top_results[1]], top_results[0]))
        if top_results[0] > self.threshold:
            return mapped_utterance
        return utterance
    
    def get_most_similar_label(self, utterance):
        """
        Returns the label of the most similar utterance to the given utterance.
        """
        query_embedding = self.embedder.encode(utterance, convert_to_tensor=True)
        cos_scores = util.pytorch_cos_sim(query_embedding, self.embeddings)[0]
        #top_result = torch.topk(cos_scores, k=5)
        #print(top_result)
        top_result = torch.max(cos_scores, dim=0)
        #print(top_result)
        print( "Query: {}, label: {}, score: {}   ".format(utterance, self.labels[top_result[1]], top_result[0]))
        if top_result[0] > self.threshold:
            label = self.labels[top_result[1]]
        else:
            label = "bad"
        return label
    
    def get_informable_slots(self):
        """
        Returns the informable slots of the domain.
        """
        return list(set(self.labels))
    
    def get_requestable_slots(self):
        """
        Returns the requestable slots of the domain.
        """
        return list(set(self.labels))
    
    def get_labels(self):
        """
        Returns the labels of the domain.
        """
        return list(set(self.labels))
    

