"""
This is a simple application for sentence embeddings: semantic search

We have a corpus with various sentences. Then, for a given query sentence,
we want to find the most similar sentence in this corpus.

This script outputs for various queries the top 5 most similar sentences in the corpus.
"""
import os
from sentence_transformers import SentenceTransformer, util
import torch
import pickle
import random
import time
from corpus import Corpus
from sklearn import metrics
import matplotlib.pyplot as plt
import numpy as np

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
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    embedder = SentenceTransformer('PM-AI/bi-encoder_msmarco_bert-base_german', device=device)
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

def make_pickeld_corpus(corpus_train, train_labels, corpus_test, test_labels, name=""):
    
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    embedder = SentenceTransformer('PM-AI/bi-encoder_msmarco_bert-base_german', device=device)
    #embedder = SentenceTransformer('aari1995/German_Semantic_STS_V2', device='cuda:0')
    corpus = corpus_train + corpus_test
    labels = train_labels + test_labels
    corpus_embeddings = get_embeddings(embedder, corpus)
    #with open(name + 'corpus_embeddings.pkl', "wb") as fOut:
    #    pickle.dump({'sentences': corpus, 'embeddings': corpus_embeddings, 'labels': labels  }, fOut, protocol=pickle.HIGHEST_PROTOCOL)
    # Create a dictionary to store embeddings and labels
    data_dict = {
        'embeddings': corpus_embeddings,
        'corpus': corpus,
        'labels': labels
    }

    # Save the dictionary to a file using torch.save()
    torch.save(data_dict, 'embeddings.pt')



def manual(embedder, corpus_train, train_labels, corpus_embeddings = None):
    while(True):

        
        if(corpus_embeddings == None):
            corpus_embeddings = get_embeddings(embedder, corpus_train)

        with open('embeddings.pkl', "wb") as fOut:
            pickle.dump({'sentences': corpus_train, 'embeddings': corpus_embeddings, 'labels': train_labels  }, fOut, protocol=pickle.HIGHEST_PROTOCOL)

        print("\nPlease write a Query:")
        query = input()
        print("query: ", query, corpus_train[0])
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

def automatic(embedder, corpus_train, train_labels, corpus_test, test_labels, corpus_embeddings = None, threshold = 0.97, name=""):

    # top_k here
    if(corpus_embeddings == None):
            corpus_embeddings = get_embeddings(embedder, corpus_train)

    with open(name + 'embeddings.pkl', "wb") as fOut:
        pickle.dump({'sentences': corpus_train, 'embeddings': corpus_embeddings, 'labels': train_labels  }, fOut, protocol=pickle.HIGHEST_PROTOCOL)

    query_embeddings = embedder.encode(corpus_test, convert_to_tensor=True)
    pred_labels = []
    scores = []
    all_labels = ['Bye', 'ChangeConfig', 'GetNextModule', 'GetProgress', 'Greet', 'Help', 'InformCompletionGoal', 'InformTimeConstraint', 'LoadMoreSearchResults', 'No',
                  'RequestTest', 'SearchForContent', 'SearchForDefinition', 'SuggestImprovement', 'SuggestRepetition', 'Thanks', 'Yes', 'Bad']
    for idx, embedding in enumerate(query_embeddings):
        cos_scores = util.cos_sim(embedding, corpus_embeddings)[0]
        top_results = torch.max(cos_scores, dim=0)
        #if top_results[0] < threshold:
        #    pred_labels.append('Bad')
        #else:
        pred_labels.append(train_labels[top_results[1]])
        scores.append(top_results[0].item())
        if train_labels[top_results[1]] != test_labels[idx]:
            print("Query: {}, Match: {}, Score: {}, True label: {}, Predicted: {}".format(corpus_test[idx], corpus_train[top_results[1]], top_results[0], test_labels[idx], train_labels[top_results[1]]))
    #print("-----------------------------------------")
    #print("Accuracy: ", sum([1 if pred_labels[i] == test_labels[i] else 0 for i in range(len(pred_labels))])/len(pred_labels))
    #print("F1: ", metrics.f1_score(test_labels, pred_labels, average='weighted', labels=all_labels))
    #print("F1_macro: ", metrics.f1_score(test_labels, pred_labels, average='macro', labels=all_labels))
    #print("F1_micro: ", metrics.f1_score(test_labels, pred_labels, average='micro', labels=all_labels))
    #print("Precision: ", metrics.precision_score(test_labels, pred_labels, average='weighted', labels=all_labels))
    #print("Recall: ", metrics.recall_score(test_labels, pred_labels, average='weighted', labels=all_labels))
    #print("Confusion Matrix: \n", metrics.confusion_matrix(test_labels, pred_labels, labels=all_labels))
    #print("number of wrongly classified without 'Bad': ", sum([1 if pred_labels[i] != test_labels[i] and pred_labels[i] != 'Bad' else 0 for i in range(len(pred_labels))]))
    #print("Classification Report: \n", metrics.classification_report(test_labels, pred_labels, labels=all_labels))
    #metrics.ConfusionMatrixDisplay.from_predictions(test_labels, pred_labels, labels=all_labels, xticks_rotation='vertical')
    #plt.savefig(embedder._get_name() + '_len_' + str(len(corpus_test)) + '_cm.png', pad_inches=0.4, bbox_inches='tight')
    #print("Length of query: ", len(query_embeddings))
    # print average score when incorrect
    print("Average score when incorrect: ", sum([scores[i] if pred_labels[i] != test_labels[i] else 0 for i in range(len(pred_labels))])/sum([1 if pred_labels[i] != test_labels[i] else 0 for i in range(len(pred_labels))]))
    #print("scores when incorrect: ", [scores[i] if pred_labels[i] != test_labels[i] for i in range(len(pred_labels))] )
   # print average score when correct
    print("Average score when correct: ", sum([scores[i] if pred_labels[i] == test_labels[i] else 0 for i in range(len(pred_labels))])/sum([1 if pred_labels[i] == test_labels[i] else 0 for i in range(len(pred_labels))]))
    #print("scores when correct: ", [scores[i] if pred_labels[i] == test_labels[i] else 0 for i in range(len(pred_labels))] )
    # print max score when incorrect
    print("Max score when incorrect: ", max([scores[i] if pred_labels[i] != test_labels[i] else 0 for i in range(len(pred_labels))]))
    # print min score when correct
    print("Min score when correct: ", min([scores[i] if pred_labels[i] == test_labels[i] else 1000 for i in range(len(pred_labels))]))
    #mistakes = sum([1 if pred_labels[i] != test_labels[i] and pred_labels[i] != 'Bad' else 0 for i in range(len(pred_labels))])
    #accuracy_without_bad = sum([1 if pred_labels[i] == test_labels[i] and pred_labels[i] != 'Bad' else 0 for i in range(len(pred_labels))])/sum([1 if pred_labels[i] != 'Bad' else 0 for i in range(len(pred_labels))])
    #count_bad = sum([1 if pred_labels[i] == 'Bad' else 0 for i in range(len(pred_labels))])
    #return mistakes, accuracy_without_bad, count_bad

def fine_tune_threshold(embedder, corpus_train, train_labels, corpus_test, test_labels, corpus_embeddings = None):
    mistakes = []
    accuracies = []
    bads = []
    for threshold in np.arange(0.96, 0.983, 0.002):
        mistake, acc, bad = automatic(embedder, corpus_train, train_labels, corpus_test, test_labels, corpus_embeddings, threshold)
        mistakes.append(mistake)
        accuracies.append(acc)
        bads.append(bad)
    # plot two curves mistakes and accuracies in one plot against threshold
    fig, ax1 = plt.subplots()
    
    color = 'tab:red'
    ax1.set_xlabel('Threshold')
    ax1.set_ylabel('Mistakes/BAD', color = color)
    ax1.plot(np.arange(0.96, 0.983, 0.002), mistakes, color = color)
    ax1.plot(np.arange(0.96, 0.983, 0.002), bads, color = 'tab:orange')
    ax1.tick_params(axis ='y', labelcolor = color)
    # mistakes - bad:
    ax1.plot(np.arange(0.96, 0.983, 0.002), [mistakes[i] - bads[i] for i in range(len(mistakes))], color = 'tab:green')
    
    plt.savefig(embedder._get_name() + '_len_' + str(len(corpus_test)) + '_mistakes.png', pad_inches=0.4, bbox_inches='tight')
    print("Minimum mistakes: ", min(mistakes), " at threshold: ", np.arange(0.96, 0.983, 0.002)[mistakes.index(min(mistakes))])
    print("Maximum accuracy: ", max(accuracies), " at threshold: ", np.arange(0.96, 0.983, 0.002)[accuracies.index(max(accuracies))])



def transform_csv(dir_path, new_dir_path):
    """
    adds "" to each line in the csv
    """
    for file in os.listdir(dir_path):
        path = os.path.join(dir_path, file)
        new_path = os.path.join(new_dir_path, file)
        with open(path, 'r') as f:
            lines = f.readlines()

        with open(path, 'w') as f:
            for line in lines:
                f.write('"' + line.strip() + '"' + '\n')
    



def main():
    corpus = Corpus()
    while(True):
        print(torch.cuda.is_available())
        print(torch.__version__)
        print("---------------------------")
        print("Do you want to... \n 1.make one csv \n 2.load corpus with strasfied sampling \n 3. Cross Validation \n 4.Cross Val across informs \n 5.load the full corpus \n 6.load cached embeddings \n 7. paranthesis csvs \n 8.exit")
        choice = input()
        
        match choice:
            case '1':
                corpus.remove_duplicates('./short_corpus/')
                corpus.make_csv('./short_corpus/', 'short_corpus')
                print("Done making csv")
                continue
            case '2':
                corpus_train, train_labels, corpus_test, test_labels = corpus.load_stratisfied('./short_corpus_paranthesis/', 'stratisfied')              
                corpus_embeddings = None
                make_pickeld_corpus(corpus_train, train_labels, corpus_test, test_labels, "short_corpus")
            case '3':
                corpus_informs = corpus.load_corpus_per_inform('./short_corpus/')
                cross_validation(corpus_informs)
            case '4':
                corpus_informs = corpus.load_corpus_per_inform('./short_corpus/')
                corpus_train, _ = corpus.load_corpus('short_corpus_train.csv')
                corpus_test, _ = corpus.load_corpus('short_corpus_test.csv')
                corpus_full = corpus_train + corpus_test
                cross_validation_across_informs(corpus_informs, corpus_full)
            case '5':
                corpus_train, train_labels = corpus.load_corpus('short_corpus_train.csv')
                corpus_test, test_labels = corpus.load_corpus('short_corpus_test.csv')
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
                transform_csv('./short_corpus/', './short_corpus_paranthesis/')
            case '8':
                exit()
            case _:
                print("Invalid input")
                continue


        print("loading model... \n")
        
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        #embedder = SentenceTransformer('distiluse-base-multilingual-cased-v2') # 539 MB
        #embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cuda') # 90.9 MB
        #embedder = SentenceTransformer('distilbert-multilingual-nli-stsb-quora-ranking') # 539 MB
        #embedder = SentenceTransformer('symanto/sn-xlm-roberta-base-snli-mnli-anli-xnli') # 1.11 GB
        #embedder = SentenceTransformer('aari1995/German_Semantic_STS_V2', device='cuda') # 1.34 GB
        #embedder = SentenceTransformer('bert-base-multilingual-uncased') # 672 MB
        #embedder = SentenceTransformer('deutsche-telekom/gbert-large-paraphrase-cosine')
        #embedder = SentenceTransformer('Sahajtomar/German-semantic')
        #embedder = SentenceTransformer('clips/mfaq')
        embedder = SentenceTransformer('PM-AI/bi-encoder_msmarco_bert-base_german', device=device)
        #embedder = SentenceTransformer('PM-AI/sts_paraphrase_xlm-roberta-base_de-en')
        #embedder = SentenceTransformer('nblokker/debatenet-2-cat')
        print("Number parameter: ", sum(p.numel() for p in embedder.parameters()))

        print("Do you want to test automatically or yourself? \n 1.automatically \n 2.yourself \n 3.fine tune threshold \n 4.exit")
        choice = input()
        match choice:
            case '1':
                automatic(embedder, corpus_train, train_labels, corpus_test, test_labels, corpus_embeddings)
            case '2':
                manual(embedder, corpus_train, train_labels, corpus_embeddings)
            case '3':
                fine_tune_threshold(embedder, corpus_train, train_labels, corpus_test, test_labels, corpus_embeddings)
            case '4':
                exit()
            case _:
                print("Invalid input")

if __name__ == '__main__':
    main()