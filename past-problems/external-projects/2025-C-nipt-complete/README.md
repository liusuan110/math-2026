# CUMCM2025C 全国大学生数学竞赛 C 题解答

## Run

### Python

本项目使用 [uv](https://github.com/astral-sh/uv) 进行包管理。

请在根目录下执行以下命令同步环境：

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv sync
```

### Report

- 论文模板需要使用配方 `Xelatex -> biber -> Xelatex -> Xelatex` 编译
- 使用 GBT7714 引用格式对 `bib`文件进行引用文献管理，详见：[参考项目](https://github.com/Andrew82106/MathorcupLatexTemplate)
- 在 VSCode 的 `settings.json` 中，添加如下条目：

```json
"latex-workshop.latex.tools": [
    {
        "name": "xelatex",
        "command": "xelatex",
        "args": [
            "-synctex=1",
            "-interaction=nonstopmode",
            "-file-line-error",
            "%DOCFILE%"
        ]
    },
    {
        "name": "biber",
        "command": "biber",
        "args": ["%DOCFILE%"]
    }
],
"latex-workshop.latex.recipes": [
    {
        "name": "xelatex -> bibtex -> xelatex*2",
        "tools": ["xelatex", "bibtex", "xelatex", "xelatex"]
    },
    {
        "name": "xelatex -> biber -> xelatex*2",
        "tools": ["xelatex", "biber", "xelatex", "xelatex"]
    }
],
```

- 若无需编译参考文献，选择 `xelatex` 即可
- 需要编译参考文献时，请在 `插件 -> LaTeX -> 构建 LaTeX 项目` 中运行 `配方: xelatex -> biber -> xelatex*2`

---

## Todo

### 参考文献

- [ ] 收集参考文献
- [ ] 为参考文献添加正确的 GBT7714 格式

```bash
python utils/parseGBT7714.py report/input.txt report/out.bib
```

- [ ] 使用配方 `xelatex -> biber -> xelatex*2` 来编译，获取正确的参考文献

### 论文

- [ ] 确保交叉引用和正文之间有空格间距

```text
如图 \cite{fig:example_1} 所示.
```

- [ ] 确保行间公式和正文之间没有空行，保持相同的间距

如 `LaTeX` 代码如下：

```latex
这里是正文：
$$
a^2 + b^2 = c^2
$$
```

- [ ] 确保所有行间公式都打上了序号！

- [ ] 确保论文中所有图示都采用 PDF 插入矢量图

### 赛中

- [ ] 下载赛题提交客户端，保证能够上传
- [ ] 确保承诺书已填写
- [ ] 生成 MD5 码并保证不再打开文档

```bash
certutil -hashfile "ARIMA.pdf" MD5
```

- [ ] 需要研究`Q4`中“染色体非整倍体(如21三体)的生物学机制及其在非性别染色体上的数据表现(如13/18/21号染色体的 Z 值、GC含量、读段数及相关比例升高)是否是独立于胎儿性别的”的问题。
- [ ] 需要研究`Q4`中男女胎儿对孕妇的BMI的影响
- [ ] 记得在`Q1`中提及不使用Pearson法的原因
- [ ] 记得要先对数据进行预处理，剔除异常值（数据预处理肯定会影响四个问题的结果，要小心点）

> 目前发现的数据预处理时需要注意的规则：
>
> 1. GC含量有异常（正常 GC 含量范围为 **40% ~ 60%**）
>
>    因为“CG含量需要在40-60，但是 人体的GC含量。一般认为在40左右，低于40的数据占了数据总量的三分之一。”所以可能考虑：对于超出范围但没超出太多的数据，也可以纳入后续计算，但计算权重需降低。具体该有多低，需要仔细考虑。
>
> 2. NIPT 产前检测技术需要在 **10-25 周**内检测才算是比较有效的
>
> 3. 女胎那里有个身高135cm的孕妇可能要注意
>
> 4. 

- [ ] 记得搜索相关论文，着重注意关键词

> ：哦对了 我们写题目一定要先看论文
> ：2022C 的那个中心对数变换 实际上是根据题目的关键词搜知网论文才搜出来的
> ：然后国奖论文全部都要有中心对数变换这个关键词
> ：它不是一个数学建模的知识点，是一个数据处理技巧，是题目给了这个成分数据的提示之后需要现场找资料找到应对这个数据应该用什么方法，那一年是只有找到了奖才高

