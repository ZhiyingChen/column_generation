# 📦 切割优化与列生成算法（Column Generation for Multi-Day Cutting Plan）

---

## 🧩 项目背景

在制造、包装、物流等行业中，常面临将大块材料（如钢卷、纸卷）裁剪为不同规格以满足每日订单需求的问题。如何优化切割模式，使原材料利用率最大化，并减少浪费与加工时间，是生产调度中的重要课题。

本项目针对该类**多天、多规格订单切割优化问题**，设计了一个基于列生成（Column Generation）的求解框架，并引入 Pyomo + Gurobi 实现多目标建模与迭代式模式生成。

---

## 📋 问题描述

- 每天有一组切割需求（不同宽度与数量）；
- 每个原料的宽度固定，切割数量有限（最多切 K 刀）；
- 残料超过最小剩余值可入库，否则当作废料；
- 每种切割模式决定一组规格的组合；
- 目标是：**在满足每日需求的前提下，最小化使用原料数量**，同时控制废料量。

---



## 🧠 模型结构

项目采用**列生成（Column Generation）框架**，分三层：

### 🔹 原始问题（Original Problem）

- 输入最终模式集；
- 建立 MILP 问题，决定每个模式的使用次数；
- 满足所有规格需求、最小化使用原材料总数。

### 🔹 主问题（Master Problem）

- 给定一组当前可用模式；
- 建立 LP 问题，变量为每种模式使用数量；
- 得到对偶值（每种规格的“影子价格”）；

### 🔹 子问题（Sub Problem）

- 利用对偶值，求解能否生成新的有“负 reduced cost”的模式；
- 其本质是一个背包问题或整数优化问题；
- 包括是否残料入库的逻辑建模。

---

## 🔁 求解流程（Context 类）

1. 对每个日期读取需求；
2. 初始化切割模式；
3. 重复执行：
   - 求解主问题 → 得到对偶值；
   - 构造子问题 → 生成新模式；
   - 若找到新模式则更新模式集；
   - 直至子问题无改进；
4. 最后求解原始问题，输出结果；
5. 可顺序或并行处理多天任务。

---


## 📌 应用场景

- 钢材、纸板、织物等大规格材料切割排程；
- 包装/物流行业按需裁剪策略优化；
- 库存管理中“残料-废料”二元分类问题；
- 箱型优化、模板切割、板材利用等相关问题。

---
**Environment Deployment**

 Install Python Executor (version >= 3.7.0), Anaconda IDE is recommended


The required packages are listed in requirements.txt. you can install them using:

    pip install -r requirements.txt
 
 **Run**

To run project:

    1. put your input data in data folder, you can adjust parameters.
    2. execute python main.py, and result.csv will be generated in data folder.