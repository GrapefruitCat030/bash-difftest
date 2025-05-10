# bash-difftest

一个自动化蜕变差分测试框架。

## 特点

- 使用语法制导的方式生成大量测试种子。
- 对 bash 和 dash (posix shell) 进行差分测试 。
- 蜕变关系从 *相同语义突变* 思想出发。
- 蜕变所用变异子通过 LLM 生成和修正。
- 变异子使用语法树解析API生成。

## 使用方式

目前提供了本地部署和容器部署两种方式。

- 本地部署（不建议）：将源码拉下来后，使用 `make init`初始化环境
  - 但由于环境复杂，不能保证不同机器上的本地部署一致。
  - 由于测试种子的不确定性，待测shell可能会对本地环境造成破坏。不建议本地部署。
- 容器部署：
  1. 使用 `docker pull grapefruitcat030/bash-difftest:dev` 拉取测试框架镜像；
  2. 进入 `/workspace` 目录，运行 `make test`，执行测试，过程可以使用 `ctrl+C` 停止测试，会自动生成测试报告到 `results/report` 目录。
  3. 测试过程中，可能存在未能正常结束运行的shell，需要运行 `scripts/monitor.py` 进行实时监测清理。
  4. 测试完毕时，可以运行 `scripts/failure_filter.py` 脚本对无关错误进行过滤, 结果同样保存到 `results/report` 目录。
  5. 测试完毕后，运行 `make coverage` 生成对应测试覆盖率报告。

## 项目架构

```mermaid
graph TD
    %% 入口与配置
    main["main.py<br>入口"] --> config_loader["配置加载<br>load_config()"]
    config_loader --> config["配置文件<br>configs/conf.json"]

    %% 运行模式
    main --> mode{"运行模式"}

    %% 准备阶段
    mode -->|prepare| prep["准备阶段<br>prepare_mutators()"]
    prep --> feature_list["特性列表<br>FeatureList"]
    
    %% MutatorGenerator 细化
    feature_list --> generator["Mutator生成器<br>MutatorGenerator"]
    generator --> mutator_code["Mutator代码"]
    mutator_code --> validator["MutatorValidator<br>验证器"]
    validator -->|通过| save_mutator["保存Mutator"]
    validator -->|失败| feedback["验证反馈"]
    feedback --> generator
    save_mutator --> mutator_files["Mutator文件<br>src/mutation_chain/mutators/"]

    %% 种子生成阶段
    main -->|seedgen| seedgen["种子生成<br>seedgen.py"]
    seedgen --> grammar_mutator["Grammar Mutator<br>tools/Grammar-Mutator"]
    grammar_mutator -->|bash_grammar.json| grammar_generator["grammar_generator-bash工具"]
    grammar_generator -->|生成| seeds_dir["Bash脚本种子<br>seeds/*.sh"]
    grammar_generator --> trees_dir["AST树文件<br>trees/"]

    %% 测试阶段
    mode -->|testing| test["测试阶段<br>run_difftest()"]
    test --> load_mutators["加载转换器<br>register_all_mutators()"]
    mutator_files -.-> load_mutators
    load_mutators --> mutation_chain["转换链<br>MutatorChain"]
    test --> seed_loader["加载测试种子<br>SeedLoader"]
    seed_loader --> seeds_dir
    seeds_dir -->|输入转换| mutation_chain
    mutation_chain --> posix_files["转换后的POSIX脚本<br>results/posix_code/"]

    %% 差分测试与报告
    seeds_dir -->|Bash| bash["Bash Shell<br>with gcov and valgrind"]
    posix_files -->|Dash| dash["Dash Shell<br>with gcov and valgrind"]
    bash --> diff_tester["差异测试器<br>DifferentialTester"]
    dash --> diff_tester
    diff_tester --> test_results["测试结果<br>results/"]
    test_results --> reporter["报告生成器<br>TestReporter"]
    reporter --> report_files["测试报告<br>results/reports/"]

    %% 失败过滤
    report_files --> failure_filter["failure_filter.py<br>自动过滤"]
    failure_filter --> filtered_reports["过滤后报告<br>results/reports/*.filtered.json"]
    filtered_reports -->|"人工检查与修正"| failure_filter

    %% 工具与依赖
    utils["通用工具<br>src/utils/"] -.-> config_loader
    utils -.-> diff_tester
    tree_sitter["Tree-Sitter<br>AST解析"] -.-> mutation_chain

    %% 样式
    classDef primary fill:#f9f,stroke:#333,stroke-width:2px;
    classDef secondary fill:#bbf,stroke:#33f,stroke-width:1px;
    classDef data fill:#dfd,stroke:#3a3,stroke-width:1px;
    classDef config fill:#ffd,stroke:#aa3,stroke-width:1px;
    classDef flow fill:#fff,stroke:#333,stroke-width:1px;

    class main,prep,test,seedgen primary;
    class generator,validator,mutation_chain,diff_tester,reporter,grammar_mutator,grammar_generator,prompt_engine,llm,failure_filter secondary;
    class feature_list,seeds_dir,mutator_files,posix_files,test_results,report_files,trees_dir,mutator_code,save_mutator,feature_in,feedback,filtered_reports,final_reports data;
    class config,utils,tree_sitter config;
    class mode,seed_loader,load_mutators flow;
    class bash,dash flow;
```