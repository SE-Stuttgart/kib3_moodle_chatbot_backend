"""
This is a simple application for sentence embeddings: semantic search

We have a corpus with various sentences. Then, for a given query sentence,
we want to find the most similar sentence in this corpus.

This script outputs for various queries the top 5 most similar sentences in the corpus.
"""
from sentence_transformers import SentenceTransformer, util
import torch
import pickle
import random
import time
from corpus import Corpus

def get_embeddings(embedder, corpus):
    #print("Encoding corpus...")
    corpus_embeddings = embedder.encode(corpus, convert_to_tensor=True)
    #corpus_embeddings = util.normalize_embeddings(corpus_embeddings)
    return corpus_embeddings

def cross_validation(corpus_per_inform):
    embedder = SentenceTransformer('PM-AI/bi-encoder_msmarco_bert-base_german')
    #embedder = SentenceTransformer('aari1995/German_Semantic_STS_V2', device='cuda:0')
    scores = []
    for inform in corpus_per_inform:
        #scores = []
        for sentence in inform[1]:
            corpus_test = inform[1].copy()
            corpus_test.remove(sentence)
            corpus_embeddings = get_embeddings(embedder, corpus_test)
            query_embedding = embedder.encode(sentence, convert_to_tensor=True)
            #query_embedding = util.normalize_embedding(query_embedding
        
            # We use cosine-similarity and torch.topk to find the highest 5 scores
            cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
            top_results = torch.topk(cos_scores, k=1)
            scores.append(top_results[0][0].item())
        #print("inform: ", inform[0])
    print("scores: ", scores)
    print("mean: ", sum(scores)/len(scores))
    print("max: ", max(scores))
    print("min: ", min(scores))
    print("\n====================================================\n")
        

def cross_validation_across_informs(corpus_per_inform, corpus_full):
    embedder = SentenceTransformer('PM-AI/bi-encoder_msmarco_bert-base_german', device='cuda:0')
    #embedder = SentenceTransformer('aari1995/German_Semantic_STS_V2', device='cuda:0')
    scores = []
    for inform in corpus_per_inform:
        #scores = []
        corpus_test = corpus_full.copy()
        for sentence in inform[1]:
            corpus_test.remove(sentence)
        print("corpus_test: ", len(corpus_test))
        corpus_embeddings = get_embeddings(embedder, corpus_test)
        for sentence in inform[1]:
            query_embedding = embedder.encode(sentence, convert_to_tensor=True)
      
            # We use cosine-similarity and torch.topk to find the highest 5 scores
            cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
            top_results = torch.topk(cos_scores, k=1)
            scores.append(top_results[0][0].item())
        
    print("scores: ", scores)
    print("mean: ", sum(scores)/len(scores))
    print("max: ", max(scores))
    print("min: ", min(scores))
    print("\n====================================================\n")



def manual(embedder, corpus_train, train_labels, corpus_embeddings = None):
    while(True):

        
        if(corpus_embeddings == None):
            corpus_embeddings = get_embeddings(embedder, corpus_train)

        with open('embeddings.pkl', "wb") as fOut:
            pickle.dump({'sentences': corpus_train, 'embeddings': corpus_embeddings, 'labels': train_labels  }, fOut, protocol=pickle.HIGHEST_PROTOCOL)

        print("\nPlease write a Query:")
        query = input()
        #query = [query]

        # Find the closest 5 sentences of the corpus for each query sentence based on cosine similarity
        top_k = min(5, len(corpus_train))
        time_start = time.time()
        query_embedding = embedder.encode(query, convert_to_tensor=True)
        #query_embedding = util.normalize_embedding(query_embedding)

        
        # We use cosine-similarity and torch.topk to find the highest 5 scores
        cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
        top_results = torch.topk(cos_scores, k=top_k)
        time_end = time.time()
        
        print("\n\n======================\n\n")
        print("Query:", query)
        print("\nTop 5 most similar sentences in corpus in ", time_end-time_start, "seconds, and on device: ", query_embedding.device)

        for score, idx in zip(top_results[0], top_results[1]):
            print(corpus_train[idx], "(Score: {:.4f})".format(score))
        """

        hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=5, score_function=util.dot_score)
        
        hits = hits[0]
        for hit in hits:
            print(corpus[hit['corpus_id']], "(Score: {:.4f})".format(hit['score']))
        """

def automatic(embedder, corpus_train, train_labels, corpus_test, test_labels, corpus_embeddings = None):
    if(corpus_embeddings == None):
            corpus_embeddings = get_embeddings(embedder, corpus_train)

    with open('embeddings.pkl', "wb") as fOut:
        pickle.dump({'sentences': corpus_train, 'embeddings': corpus_embeddings, 'labels': train_labels  }, fOut, protocol=pickle.HIGHEST_PROTOCOL)

    query_embeddings = embedder.encode(corpus_test, convert_to_tensor=True)
    pred_labels = []

    for idx, embedding in enumerate(query_embeddings):
        cos_scores = util.cos_sim(embedding, corpus_embeddings)[0]
        top_results = torch.max(cos_scores, dim=0)
        pred_labels.append(train_labels[top_results[1]])
        if train_labels[top_results[1]] != test_labels[idx]:
            print("Query: {}, Match: {}, Score: {}, True label: {}, Predicted: {}".format(corpus_test[idx], corpus_train[top_results[1]], top_results[0], test_labels[idx], train_labels[top_results[1]]))

    print("Accuracy: ", sum([1 if pred_labels[i] == test_labels[i] else 0 for i in range(len(pred_labels))])/len(pred_labels))
    print("Length of query: ", len(query_embeddings))


def main():
    corpus = Corpus()
    while(True):
        print(torch.cuda.is_available())
        print(torch.__version__)
        print("---------------------------")
        print("Do you want to... \n 1.make one csv \n 2.load corpus with strasfied sampling \n 3. Cross Validation \n 4.Cross Val across informs \n 5.load the full corpus \n 6.load cached embeddings \n 7.exit")
        choice = input()
        
        match choice:
            case '1':
                corpus.make_csv('./corpus/', 'corpus')
                print("Done making csv")
                continue
            case '2':
                corpus_train, train_labels, corpus_test, test_labels = corpus.load_stratisfied('./big_corpus/', 'stratisfied')              
                corpus_embeddings = None
            case '3':
                corpus_informs = corpus.load_corpus_per_inform('./corpus/')
                cross_validation(corpus_informs)
            case '4':
                corpus_informs = corpus.load_corpus_per_inform('./corpus/')
                corpus_train, _ = corpus.load_corpus('corpus_train.csv')
                corpus_test, _ = corpus.load_corpus('corpus_test.csv')
                corpus_full = corpus_train + corpus_test
                cross_validation_across_informs(corpus_informs, corpus_full)
            case '5':
                corpus_train, train_labels = corpus.load_corpus('big_corpus_train.csv')
                corpus_test, test_labels = corpus.load_corpus('big_corpus_test.csv')
                corpus_embeddings = None
                print("corpus_train: ", len(corpus_train))
                print("corpus_test: ", len(corpus_test))
                print("train_labels: ", len(train_labels))
                print("test_labels: ", len(test_labels))

            case '6':
                with open('embeddings.pkl', "rb") as fIn:
                    stored_data = pickle.load(fIn)
                    corpus_train = stored_data['sentences']
                    corpus_embeddings = stored_data['embeddings']
                    train_labels = stored_data['labels']
                corpus_test, test_labels = corpus.load_corpus('big_corpus_test.csv')
            case '7':
                exit()
            case _:
                print("Invalid input")
                continue


        print("loading model... \n")
        
        #embedder = SentenceTransformer('distiluse-base-multilingual-cased-v2') # 539 MB
        embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cuda') # 90.9 MB
        #embedder = SentenceTransformer('distilbert-multilingual-nli-stsb-quora-ranking') # 539 MB
        #embedder = SentenceTransformer('symanto/sn-xlm-roberta-base-snli-mnli-anli-xnli') # 1.11 GB
        #embedder = SentenceTransformer('aari1995/German_Semantic_STS_V2', device='cuda') # 1.34 GB
        #embedder = SentenceTransformer('bert-base-multilingual-uncased') # 672 MB
        #embedder = SentenceTransformer('deutsche-telekom/gbert-large-paraphrase-cosine')
        #embedder = SentenceTransformer('Sahajtomar/German-semantic')
        #embedder = SentenceTransformer('clips/mfaq')
        #embedder = SentenceTransformer('PM-AI/bi-encoder_msmarco_bert-base_german', device='cuda')
        #embedder = SentenceTransformer('PM-AI/sts_paraphrase_xlm-roberta-base_de-en')
        #embedder = SentenceTransformer('nblokker/debatenet-2-cat')
        print("Number parameter: ", sum(p.numel() for p in embedder.parameters()))

        print("Do you want to test automatically or yourself? \n 1.automatically \n 2.yourself \n 3.exit")
        choice = input()
        match choice:
            case '1':
                automatic(embedder, corpus_train, train_labels, corpus_test, test_labels, corpus_embeddings)
            case '2':
                manual(embedder, corpus_train, train_labels, corpus_embeddings)
            case '3':
                exit()
            case _:
                print("Invalid input")

if __name__ == '__main__':
    main()