import hashlib
import re
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pygments.lexers import PythonLexer
from pygments import lex
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import logging
import time




# 配置日志以避免显示jieba的详细调试信息
logging.getLogger('jieba').setLevel(logging.WARNING)

class TextSimilarityCalculator:
    def __init__(self, text_corpus, hashbits=128, cosine_weight=0.6, hamming_weight=0.4, workers=10, min_df=0.02, max_df=0.8):
        self.hashbits = hashbits  # SimHash位数，用于确定特征向量的长度
        self.cosine_weight = cosine_weight  # 余弦相似度权重，在最终得分计算中的占比
        self.hamming_weight = hamming_weight  # 汉明距离权重，在最终得分计算中的占比
        self.workers = workers  # 线程池工作线程数，用于并行处理任务
        self.text_corpus = self.parallel_tokenize(text_corpus)  # 对输入的文本数据进行并行分词处理
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_df=max_df, min_df=min_df)  # TF-IDF向量化，包括双字节n-gram
        self.tfidf_matrix = self.vectorizer.fit_transform(self.text_corpus)  # 根据分词结果生成TF-IDF矩阵
        self.feature_names = self.vectorizer.get_feature_names_out()  # 获取TF-IDF矩阵中的特征名称
        self.document_hashes = self.calculate_simhashes_parallel()  # 并行计算文档的SimHash值

    def parallel_tokenize(self, texts):
        # 使用线程池来加速分词过程
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            results = list(executor.map(lambda text: ' '.join(jieba.cut(text)), texts))
        return results

    def hashfunc(self, x):
        # 定义一个哈希函数，使用SHA-256算法，用于SimHash计算中
        hash_value = hashlib.sha256(x.encode('utf-8')).hexdigest()
        return int(hash_value, 16)

    def simhash(self, features):
        v = [0] * self.hashbits  # 初始化特征向量
        for weight, feature in features:
            h = self.hashfunc(feature)  # 对每个特征应用哈希函数
            for i in range(self.hashbits):
                bitmask = 1 << i
                if h & bitmask:
                    v[i] += weight
                else:
                    v[i] -= weight
        fingerprint = 0
        for i in range(self.hashbits):
            if v[i] >= 0:
                fingerprint += 1 << i  # 根据特征向量的正负生成指纹
        return fingerprint

    def calculate_simhashes_parallel(self):
        # 并行计算所有文档的SimHash值
        tfidf_corpus = self.compute_tfidf_corpus()
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            results = list(executor.map(self.compute_simhash, tfidf_corpus))
        return results

    def compute_simhash(self, document):
        # 计算单个文档的SimHash值
        weighted_features = [(weight, feature) for feature, weight in document.items()]
        return self.simhash(weighted_features)

    def compute_tfidf_corpus(self):
        # 将TF-IDF矩阵转换为特征字典，用于后续SimHash计算
        documents = []
        for row in self.tfidf_matrix:
            feature_weights = row.toarray()[0]
            document = {feature: weight for feature, weight in zip(self.feature_names, feature_weights) if weight > 0}
            documents.append(document)
        return documents

    def calculate_scores(self):
        # 计算每个文档的综合相似度得分
        num_docs = self.tfidf_matrix.shape[0]
        cosine_sim_matrix = cosine_similarity(self.tfidf_matrix)  # 计算余弦相似度矩阵
        scores = []

        for i in range(num_docs):
            hamming_distances = [self.hamming_distance(self.document_hashes[i], self.document_hashes[j]) for j in range(num_docs) if i != j]
            total_hamming = sum(hamming_distances)
            average_cosine = (sum(cosine_sim_matrix[i]) - 1) / (num_docs - 1)
            average_hamming = total_hamming / (num_docs - 1)

            normalized_hamming = 1 - average_hamming / self.hashbits
            final_score = self.cosine_weight * average_cosine + self.hamming_weight * normalized_hamming
            scores.append(final_score * 100)

        return scores

    def hamming_distance(self, hash1, hash2):
        # 计算两个SimHash值之间的汉明距离
        x = hash1 ^ hash2
        bitmask = (1 << self.hashbits) - 1
        x &= bitmask
        return bin(x).count('1')


class CodeSimilarityCalculator:
    def __init__(self, code_corpus, workers=10):
        self.workers = workers
        self.code_corpus = [self.clean_code(code) for code in code_corpus]
        self.tokens = self.tokenize_codes(self.code_corpus)

    def clean_code(self, code):
        # 示例：移除Python或C++风格的注释
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)  # C++ 单行注释
        code = re.sub(r'#.*?$', '', code, flags=re.MULTILINE)  # Python 单行注释
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.MULTILINE | re.DOTALL)  # C++ 多行注释
        return code

    def tokenize_codes(self, codes):
        lexer = PythonLexer()
        return [set(token[1] for token in lex(code, lexer)) for code in codes]

    def calculate_jaccard_scores(self):
        scores = []
        for i in range(len(self.tokens)):
            score_list = []
            for j in range(len(self.tokens)):
                if i != j:
                    intersection = len(self.tokens[i].intersection(self.tokens[j]))
                    union = len(self.tokens[i].union(self.tokens[j]))
                    score_list.append(intersection / union if union != 0 else 0)
            scores.append(np.mean(score_list) * 100 if score_list else 0)
        return scores
