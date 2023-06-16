from sentence_transformers import SentenceTransformer, util
import pickle
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
        self.model = embedder_model
        self.embedder = SentenceTransformer(embedder_model)
        self.threshold = 0.96
        file_path = os.path.join(os.getcwd(), 'corpus_embeddings.pkl')
        print(file_path)
        with open(file_path, "rb") as fIn:
            stored_data = pickle.load(fIn)
            self.corpus = stored_data['sentences']
            self.embeddings = stored_data['embeddings']
            self.labels = stored_data['labels']
    
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
        top_results = torch.topk(cos_scores, k=1)
        print( "Query: {}, label: {}, score: {}   ".format(utterance, self.labels[top_results[1]], top_results[0]))
        if top_results[0] > self.threshold:
            label = self.labels[top_results[1]]
        else:
            label = "bad"
        return label
    
    

