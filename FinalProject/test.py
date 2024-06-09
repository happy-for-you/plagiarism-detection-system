import sys
import os
import time
import matplotlib.pyplot as plt
from matplotlib import font_manager
from algorithm import TextSimilarityCalculator, CodeSimilarityCalculator

# 添加模块路径到 PYTHONPATH
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if module_path not in sys.path:
    sys.path.append(module_path)

# 配置中文字体
font_path = 'C:\\Windows\\Fonts\\simhei.ttf'  # 替换为你的字体路径
if os.path.exists(font_path):
    font_prop = font_manager.FontProperties(fname=font_path)
else:
    font_prop = font_manager.FontProperties(family='SimHei')  # 备用方案，可能需要调整

# 生成样本数据
sample_texts = ["这是一个测试文本。"] * 100  # 简单重复文本以模拟负载
sample_codes = [
    """
    def add(a, b):
        # 这是一个加法函数
        return a + b
    """
] * 100  # 简单重复代码以模拟负载

# 测试函数
def test_performance(text_corpus, code_corpus, thread_counts):
    text_times = []
    code_times = []

    for workers in thread_counts:
        # 测试 TextSimilarityCalculator
        start_time = time.time()
        text_calc = TextSimilarityCalculator(text_corpus, workers=workers, min_df=0.01, max_df=1.0)
        text_scores = text_calc.calculate_scores()
        text_time = time.time() - start_time
        text_times.append(text_time)

        # 测试 CodeSimilarityCalculator
        start_time = time.time()
        code_calc = CodeSimilarityCalculator(code_corpus, workers=workers)
        code_scores = code_calc.calculate_jaccard_scores()
        code_time = time.time() - start_time
        code_times.append(code_time)

    return text_times, code_times

# 不同线程池大小
thread_counts = [1, 2, 3, 4, 5]  # 仅选择5组线程池大小

# 测试性能
text_times, code_times = test_performance(sample_texts, sample_codes, thread_counts)

# 可视化结果
plt.figure(figsize=(10, 5))
plt.plot(thread_counts, text_times, label='文本相似度计算时间')
plt.plot(thread_counts, code_times, label='代码相似度计算时间')
plt.xlabel('线程数', fontproperties=font_prop)
plt.ylabel('执行时间（秒）', fontproperties=font_prop)
plt.title('不同线程池大小的相似度计算性能测试', fontproperties=font_prop)
plt.legend(prop=font_prop)
plt.grid(True)
plt.show()
