import random
from sentence_transformers import SentenceTransformer, util
import os

class Corpus:
    def __init__(self):
        self.corpus_train = []
        self.train_labels = []
        self.test_labels = []
        self.corpus_test = []
        
    def make_csv(self, source_dir, destination_dir, split=0.8):
            files = os.listdir(source_dir)
            corpus = []
            informs = []
            for filename in files:
                with open(source_dir + filename, 'r', encoding="utf-8") as f_in:
                    for line in f_in:
                        corpus.append(line.replace('\n', ''))
                        informs.append(filename.replace('.csv', ''))
            index = [i for i in range(0, len(corpus))]
            random.shuffle(index)
            self.train_idx = index[:int(len(corpus)*split)]
            self.test_idx = index[int(len(corpus)*split):]
            with open(destination_dir + '_train.csv', 'w', encoding="utf-8") as fout:
                for i in self.train_idx:
                    fout.write(corpus[i] + '; ' + informs[i] + '\n')
            with open(destination_dir + '_test.csv', 'w', encoding="utf-8") as fout:
                for i in self.test_idx:
                    fout.write(corpus[i] + '; ' + informs[i] + '\n')  
            
        #
        #return self.corpus_train, self.corpus_test
    
    def load_corpus(self, file):
        corpus = []
        labels = []
        with open(file, 'r', encoding="utf-8") as f:
            for line in f:
                line = line.split('; ')
                corpus.append(line[0])
                labels.append(line[1].replace('\n', ''))
        return corpus, labels
    
    def remove_duplicates(self, source_dir):
        files = os.listdir(source_dir)
        for filename in files:
            corpus = []
            with open(source_dir + filename, 'r', encoding="utf-8") as f_in:
                for line in f_in:
                    corpus.append(line.replace('\n', ''))
            corpus = list(set(corpus))
            with open(source_dir + filename, 'w', encoding="utf-8") as fout:
                for i in range(0, len(corpus)):
                    fout.write(corpus[i] + '\n')
    
    def load_stratisfied(self, source_dir, destination_dir, split=0.8):
        files = os.listdir(source_dir)
        corpus = []
        for filename in files:
                corpus_temp = []
                with open(source_dir + filename, 'r', encoding="utf-8") as f_in:
                    for line in f_in:
                        corpus_temp.append(line.replace('\n', ''))
                corpus.append((filename.replace('.csv', ''), corpus_temp))
        corpus_train = []
        train_labels = []
        corpus_test = []
        test_labels = []
        for inform in corpus:
            index = [i for i in range(0, len(inform[1]))]
            random.shuffle(index)
            train_idx = index[:int(len(inform[1])*split)]
            test_idx = index[int(len(inform[1])*split):]
            for i in train_idx:
                corpus_train.append(inform[1][i])
                train_labels.append(inform[0])
            for i in test_idx:
                corpus_test.append(inform[1][i])
                test_labels.append(inform[0])
        with open(destination_dir + '_train.csv', 'w', encoding="utf-8") as fout:
            for i in range(0, len(corpus_train)):
                fout.write(corpus_train[i] + '; ' + train_labels[i] + '\n')
        with open(destination_dir + '_test.csv', 'w', encoding="utf-8") as fout:
            for i in range(0, len(corpus_test)):
                fout.write(corpus_test[i] + '; ' + test_labels[i] + '\n')
        
        return corpus_train, train_labels, corpus_test, test_labels
            
    def load_corpus_per_inform(self, source_dir):
        files = os.listdir(source_dir)
        corpus = []
        for filename in files:
                corpus_temp = []
                with open(source_dir + filename, 'r', encoding="utf-8") as f_in:
                    for line in f_in:
                        corpus_temp.append(line.replace('\n', ''))
                corpus.append((filename.replace('.csv', ''), corpus_temp))
        return corpus
        

        
    def save_corpus(self, train_file, test_file):
        with open(train_file, 'w') as f:
            f.write(self.corpus_train)
        with open(test_file, 'w') as f:
            f.write(self.corpus_test)
    
    def get_corpuses(self):
        return self.corpus_train, self.corpus_test
    
    def resplit(self, split=0.8):
        corpus = self.corpus_train + self.corpus_test
        corpus = random.shuffle(self.corpus)
        self.corpus_train = self.corpus[:int(len(self.corpus)*split)]
        self.corpus_test = self.corpus[int(len(self.corpus)*split):]
        return self.corpus_train, self.corpus_test
    
