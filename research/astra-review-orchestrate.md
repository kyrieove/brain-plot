# orchestrate 独立审查报告

审查日期：2026-10-01。仓库：`C:\Users\ASUS\.claude\skills\orchestrate`；HEAD：`35b46c990acb23f4b1f63a3c616a1a13aa65f096`。

先读取了 SKILL.md、scripts/orchestrate.py、scripts/test_orchestrate.py，并应用 karpathy-guidelines。未修改仓库代码。验证使用 Windows、本机 Python 3.10.11、临时 Git 仓库、假执行器及进程内替身；未调用真实模型。原有 15 个场景全部通过，但以下多个失败场景仍可复现。CLI 参数只核对了本机 `codex exec --help` / `resume --help`，未验证真实服务的额度响应或会话权限继承。

结论：目前不适合直接对含重要数据、未提交工作或并发任务的仓库无人值守运行。主要缺陷在执行边界、锁、超时和验收证据。以下共 15 条，按严重程度排序；P1 为应优先修复的可靠性/安全问题，P2 为功能或成本问题。

1. **[P1] 任务卡的文件范围和只读声明没有执行层保护，执行器可以越界修改数据。**

   **位置：** `scripts/orchestrate.py:158,178,363,428`；`SKILL.md:53,54,95`。
   
   **失败场景：** agy 使用 `--dangerously-skip-permissions`，直接在用户工作目录运行。“May change”“Read-only”“Do not commit”只是提示词，解析器也不提取这些约束。执行器误删输入数据、执行 reset/clean、修改检查脚本以通过测试、改写任务卡或控制文件时，当前脚本没有拦截。Codex 的 workspace-write 也不等于只允许任务卡列出的文件。随后 check 在宿主权限下执行，不能因 builder 有沙箱就视为安全。此项是静态确认的权限设计问题，不声称已经造成数据损失。

   **修法：** 固定并校验原始任务卡与验收命令；在独立工作副本中执行，提取明确允许写入的路径，逐轮及结束时检查完整文件变更。重要输入数据和控制状态放到执行器不能写的位置。需要真正只读保证时使用 Windows 账户/ACL 或受限执行环境；worktree 只能隔离工作改动，不能单独充当安全沙箱。禁止默认关闭 agy 权限检查。

   **测试缺口：** 加入越界修改、只读数据删除、篡改 card/check、创建提交等负例，要求拒绝验收且原数据不变。现有测试的假执行器甚至会在 review 阶段写 result.txt，仍可通过。

2. **[P1] 锁的存活判断不适用于 Windows，陈旧锁回收还存在双持锁竞争。**

   **位置：** `scripts/orchestrate.py:49-81,548-552`；`scripts/test_orchestrate.py:200-203`。
   
   **失败场景：** 本机实测，一个已经 wait() 完成的子进程，其 PID 传入 alive() 仍返回 True，因而崩溃遗留的锁可能被当作活锁，阻止后续运行。CPython 3.10.11 的 Windows 实现中，信号 0 进入控制台事件路径，不是 POSIX 的无副作用存在性查询，见 [CPython 源码](https://github.com/python/cpython/blob/v3.10.11/Modules/posixmodule.c#L7377)。另一个独立问题是“读旧锁→判断死亡→删除”不原子：两个竞争者同时读取旧锁，A 删除并创建新锁后，B 仍会删除 A 的锁再取得锁。通过控制两个线程的交错顺序，已复现两次 take_lock 都成功返回。finally 又无条件删除当前路径，可能进一步删除另一运行的锁。

   **修法：** Windows-only 的最小方案是保持打开的锁文件句柄并用标准库 msvcrt 的非阻塞字节范围锁，进程退出由系统释放；不要靠 PID 判断后 unlink 回收，也不要在释放时删掉可能已换主的路径。锁文件放到统一仓库控制位置。若保留 PID 信息，仅作为诊断，并用 ctypes 调用 Windows 查询 API 验证身份。

   **测试缺口：** 目前只测试“现存锁指向当前父进程”，没有死亡 PID、持锁者崩溃、两个竞争者同时回收或旧持锁者迟到释放的测试。此处没有把“所有 Windows 的 kill(pid,0) 都会杀进程”当作结论；本机并未复现这一说法。

3. **[P1] check 和 Git 命令没有超时，任务可以永远持锁。**

   **位置：** `scripts/orchestrate.py:17-18,428`；`scripts/test_orchestrate.py:139-140,153,159-160`。
   
   **失败场景：** 测试死循环、等待 stdin、启动长期服务，或 Git checkout hook 卡住后，subprocess.run 永不返回。timeout_min 只用于模型 CLI，对这里无效。即使每次 CLI 都按时返回，逐次重新给完整的 60 分钟也没有限制整个任务总时长。

   **修法：** 为整个任务设置基于 time.monotonic() 的 deadline，各阶段使用剩余时间；为 check、Git 和 CLI 都设置上限，并配合第 4 条清理子进程。超时必须进入统一终态并输出当前摘要。

   **测试缺口：** 使用实际阻塞的 check、挂起的 Git hook 和总预算耗尽场景，由外层 watchdog 断言按时返回、进程消失、锁可重新获取。现有名为 timeout 的场景只睡 1.2 秒，阈值却是 60 秒，实际上没有触发超时。

4. **[P1] CLI 超时只结束直接子进程，Windows 子孙进程和管道能让超时失效。**

   **位置：** `scripts/orchestrate.py:165-187,252-255,548-550`。
   
   **失败场景：** .cmd 包装器启动真正 CLI，CLI 又启动测试或脚本。subprocess.run 的超时清理不保证终止整棵进程树；子孙进程继承 stdout/stderr 管道时，回收输出还会继续等待。实测：假 CLI 生成一个继承管道、睡 2 秒的子进程，timeout=0.2，call() 到约 2.22 秒才抛错。子孙若不退出，可以无限拖延；若已关闭管道但继续工作，则可能在 orchestrator 放锁后继续修改仓库。

   **修法：** 在 Windows 用 Job Object 管理整个任务进程树，设置 kill-on-close，确保子进程在开始执行前被纳入；可用 ctypes，仍不需要第三方 Python 库。取消和超时时先停止整棵树，再回收输出、写终态和放锁。限制输出缓冲，避免无限 capture_output 耗尽内存。

   **测试缺口：** 测试 .cmd→CLI→孙进程、继承管道、关闭管道后继续写文件、取消等情况。原测试仅有单进程短睡眠。

5. **[P1] 新增文件不进入审查，Claude 的最终 diff 命令又看不到未提交实现。**

   **位置：** `scripts/orchestrate.py:440-441,523-524,258-266`；`SKILL.md:74,81`。
   
   **失败场景：** builder 新建 result.txt 但不 git add；git diff base 不包含 untracked。已复现：文件确实存在，review 收到空 diff，summary 为 PASS / DIFF: no changes。这是新增模块最常见的路径。与此同时，技能禁止执行器提交，却让 Claude 查看 main...orch/<name>：三点比较只比较提交树，正常的未提交代码改动也不会出现，而且并非所有仓库都有 main。摘要最多列前三条 diffstat，也不能可靠呈现所有改动文件。

   **修法：** 保存明确基线提交，采集 tracked、staged、untracked 的完整变更清单及新增文件内容；保留二进制文件信息和必要的产物验证。审查器和 Claude 使用同一份机器生成的清单，并对该清单检查允许修改范围。最终验收比较保存基线与当前工作内容，不使用 main...branch 代替工作区检查。

   **测试缺口：** 新增模块、第四个以后越界文件、二进制产物、暂存/未暂存混合变更都应覆盖。happy 测试恰好只创建 untracked 文件，却从不验证审查材料包含它。

6. **[P1] 分支操作没有干净基线，也没有把任务绑定到原始提交。**

   **位置：** `scripts/orchestrate.py:331-337,440,523`。
   
   **失败场景：** 开始前不检查脏工作区，用户已有未提交改动会带入 orch 分支，执行器可继续改坏这些改动。已有 orch/<name> 时直接 checkout，可能取回旧任务的提交，而不是本次来源。已复现：旧分支中的 old.txt 和用户自己改过的 check.py 都被纳入本次 diff，任务仍 PASS。base 保存的是可移动分支名；在同一 orch 分支重跑时，若其间已有提交，之前的任务改动可能不再进入 diff。detached HEAD 时 base 为空，创建分支也会失败。

   **修法：** 启动时记录 HEAD 的不可变 SHA 与来源状态。最简单的安全实现是要求工作区干净，对现有同名分支拒绝启动；需要恢复时，使用与任务卡摘要、基线 SHA 绑定的显式状态。不能要求用户清空工作区的场景则使用独立工作副本，不自动 stash、reset 或覆盖用户工作。

   **测试缺口：** 增加脏 tracked/untracked 文件、已有同名分支、非 main 默认分支、detached HEAD，以及完成部分提交后恢复运行的测试。

7. **[P1] 正常的暂停/失败出口不更新 summary，旧 PASS 会被再次输出。**

   **位置：** `scripts/orchestrate.py:348-357,392-394,423-425,455-457,509-520,577-580`。
   
   **失败场景：** 多个 timeout、quota、plan-ready、invalid verdict 分支直接 return 2，只有 status 更新；summary 只在 PASS/FAIL 或异常处理里生成。已有一次 PASS 后再次运行并超时，原 PASS 摘要仍留在磁盘，main 随后照样打印它。已通过预置 PASS 摘要并触发 TimeoutError 复现。首次运行则没有 summary，Claude 必须额外查 status/log 才能定位问题。

   **修法：** 每次 invocation 使用 run_id，取得锁后初始化当前状态；所有出口统一写带 run_id、终态、原因、check 状态、实际执行器的摘要。main 只打印当前 invocation 的摘要，原子替换状态文件。started 也应在成功取得锁后写，避免失败的第二次启动篡改正在运行任务的时间。

   **测试缺口：** 对每个 exit=2 路径同时断言摘要存在、对应当前运行、不会含旧 PASS；增加“同一目录先成功再超时/额度失败”的连续调用测试。

8. **[P1] 额度切换会选回已耗尽额度的 Codex，实际 reviewer 与摘要也可能不一致。**

   **位置：** `scripts/orchestrate.py:14,303-313,409-417,438-454,489-511,524`。
   
   **失败场景：** Codex builder 额度耗尽→agy builder 成功→same_source 强制 Codex Astra review→再次额度失败→所谓切换仍强制 Codex。已复现调用序列 codex build→agy build→codex review→codex review。默认 agy build / codex review 中，只要 Codex 额度耗尽，切到 agy reviewer 也会被强制改回 Codex。没有依据证明换模型一定有独立额度。此外，变量 reviewer 可能为 agy，但实际由 codex 审查，summary 却打印 reviewer。QUOTA 在非零退出时匹配整段自由文本，普通“修改 401/429 处理失败”也可能误判为额度问题。

   **修法：** 用明确的 provider 可用性状态和有限候选列表选择执行器；切换后不再调用本轮已确认耗尽的 provider。仅剩一方时，按明确策略用该方的新会话审查并标记，或准确返回“缺少可用 reviewer”。按真实错误字段/约定诊断识别额度，持久化实际执行器与 model 供摘要使用；同 builder/reviewer 的初始任务卡应校验或明确支持。

   **测试缺口：** 现 quota 假 Codex 只在 build 阶段报额度错，review 又永远成功，掩盖了 provider 全局额度耗尽。需要双向切换、reviewer 额度耗尽、双方耗尽、普通报错包含 quota/401/429 的测试。

9. **[P2] builder 明确报告 blocked 或根本不生成报告，仍可 PASS。**

   **位置：** `scripts/orchestrate.py:117-130,364-365,427-437,522-526`。
   
   **失败场景：** report.md 要求有 STATUS，但脚本只读取 OPEN，从不校验 done/blocked。已复现 quick 任务中 builder 输出 STATUS: blocked / OPEN: input missing，check.py 恰好退出 0，最终返回 0 和 RESULT: PASS。常见于检查命令覆盖不足、缺输入、无需执行到新分支的旧测试。quick 摘要仍显示配置的 reviewer，尽管根本没执行 review。

   **修法：** 要求当前运行产生有效报告；blocked 应返回明确的待处理终态，不进入成功判定。由 runner 记录检查结果和 review 是否实际执行，不信任模型自报 CHECK。验收命令必须证明任务目标；允许确实无需修改的任务，但要有可验证依据。

   **测试缺口：** 增加 blocked、缺报告、旧报告、格式错误和 quick review-skipped 测试。现 happy 假执行器不写 report.md，也照样被视为成功。

10. **[P2] 会话续用只覆盖内部修复轮次，恢复运行和“新会话审查”语义不一致。**

   **位置：** `scripts/orchestrate.py:215-240,252-255,385,448-454`；`SKILL.md:36-37,71-72`。
   
   **失败场景：** 第一次运行超时或额度中断后再次 run，round_no 从 0 开始，builder_session 被强制设为 None，因而重读项目、重做已做工作。session ID 只在进程成功退出后保存，已经创建会话但后来失败/超时的 ID 会丢失。相反 reviewer 在新 invocation 仍会直接读取旧 session。切换后宣称 same-source 使用 fresh session，但普通 review 分支没有在进入该模式时清旧 reviewer session，可能续用之前的 Codex 审查上下文。

   **修法：** 将会话绑定到任务卡内容摘要、基线 SHA、角色和实际 provider；恢复同一任务时续用匹配会话，任务变化则清除。在读到 thread/conversation 创建事件时就保存 ID，不等最终成功；进入要求独立审查的模式时显式新建会话。只实现“新任务”和“恢复同一任务”两种状态即可。

   **测试缺口：** 现测试只有一次 run 内的续用，没有跨 invocation 恢复、失败但已生成 session ID、任务卡修改后续用、既有 reviewer session 下进入 same-source 的情况。

11. **[P2] Windows .cmd 的参数列表包装在多处含空格时失效。**

   **位置：** `scripts/orchestrate.py:133-139,165-166`；`scripts/test_orchestrate.py:35-38,136-140`。
   
   **失败场景：** ORCH_CODEX 指向“bin with space/codex.cmd”，项目目录也包含空格时，当前 [cmd.exe, /c, *argv] 的引号组合不能可靠作为 cmd 命令行传递。已用只执行 echo OK 的假 .cmd 复现：返回 1，错误将路径截到“.../bin”，模型根本没启动。只有 executable 路径含空格的较简单情况在本机通过，不能据此认为所有空格路径都安全。

   **修法：** 优先直接调用实际 codex.exe；确需 .cmd 时，建立并测试 cmd /d /s /c 所需的完整引用和转义规则，不把普通 Windows argv 转义当成 cmd shell 转义。不用 POSIX shlex.quote 解决这个问题。

   **测试缺口：** 当前假 CLI 一律是 .py，完全绕过 .cmd 分支。增加 executable、repo、run 同时含空格及中文，以及 &、括号等 shell 字符的路径测试。

12. **[P2] 指定父进程 UTF-8 解码并不会让 Windows 子进程输出 UTF-8，replace 会静默损坏证据。**

   **位置：** `scripts/orchestrate.py:18,145-148,185-187,428-430,556-557`；`scripts/test_orchestrate.py:45-46,95-96,246-253`。
   
   **失败场景：** check 调用按 CP936/其他本地代码页输出的程序时，强制 UTF-8 + errors=replace 将中文文件名、断言信息替换成乱码，再把乱码交给 builder 修复。已用输出 GBK“测试失败”的子进程复现。给当前 orchestrator 的 stdout reconfigure 不改变子进程编码。测试里的假执行器主动 reconfigure 为 UTF-8，因而没有验证这个风险。

   **修法：** 对受控 Python 子进程显式设置 PYTHONUTF8/PYTHONIOENCODING；对其他工具约定输出编码或保留原始字节，并依据已知编码解码。协议 JSON 不应静默 replace，解析失败应留下可诊断的原始输出；普通日志可显示替代字符，但必须保留原件。

   **测试缺口：** 加入本地代码页输出、非 UTF-8 文件名/错误信息、中文 stdin 和截断 JSON，验证回传给修复器的信息没有失真。

13. **[P2] review 被统一禁用工具，却未提供足够材料；完整 diff 在续用会话中重复发送也浪费上下文。**

   **位置：** `scripts/orchestrate.py:283-300,440-454,476-485`。
   
   **失败场景：** 修复跨模块接口时，普通 diff 只有少量上下文，reviewer 看不到未改动的调用者、依赖、完整测试或生成产物，又被告知不能读文件。AGENTS.md 只对 agy 显式附前 200 行，关键约束可能被截掉。对于默认 Codex reviewer，这个 no-tools 限制并非 agy 无工具模式的必要性所要求。提示同时要求“不能用工具”和“Write review.md”，容易造成无效 verdict 再试。每次 resume 和格式重试又发送完整累计 diff，放大会话历史，却没有补齐缺失证据。

   **修法：** 将 agy 的无工具兼容要求限制在 agy；Codex reviewer 可在只读沙箱中检查当前允许范围及必要调用者。若坚持全部无工具，runner 必须提供完整变更和必要上下文并明确返回文本，由 runner 写 review.md。格式错误只请求重排 verdict，不重新做整次审查；续审发送变更增量并明确当前快照。

   **测试缺口：** 假 reviewer 大多无条件 PASS，没有任何测试让它因缺少新增文件、上下文或关键规则而 FAIL，也没有验证修复后的实际代码正确性。

14. **[P2] 测试通过主要证明控制流能跑通，不能证明“任务完成且安全”。**

   **位置：** `scripts/test_orchestrate.py:23,41-88,91-133,147-160,178-189,212-259`。
   
   **失败场景：** 默认 check 永远成功，多数 reviewer 无条件 PASS，假执行器不遵守报告契约且可在 review 中写代码；断言主要检查退出码、ROUNDS 和关键字。timeout 不触发超时，quota 不模拟 provider 全阶段耗尽。因而本次原套件全过，与空 diff PASS、blocked PASS、旧 PASS、错误切换等复现同时成立。测试本身的 subprocess.run 也没有 watchdog，加入真实挂起场景后可能把测试套件卡死。

   **修法：** 保留现有少量控制流 smoke tests；增加围绕不变量的验收测试：只能允许文件改变、全部改动可审、失败不会 PASS、终态摘要必写、进程与锁必释放、切换不回到失效 provider。让 check 真正读取产物并检验内容；假 reviewer 必须根据输入材料作出确定性判断。由外层进程限制整个测试时间。CLI 参数兼容性另外用无模型调用的 --help 和 .cmd 包装器检查。

   **测试缺口：** 优先补第 2、3、4、5、7、8、9 条的回归，而不是继续增加只验证摘要关键字的场景。本报告不把这些假执行器测试当作真实 agy/Codex 行为已经得到验证。

15. **[P2] planned 流程和重复人工门槛与“Claude 只派卡及终验”目标冲突，可删掉一层流程。**

   **位置：** `SKILL.md:19-22,67,84-85`；`scripts/orchestrate.py:338-357,366-367,408,421,458,508`。
   
   **失败场景：** 任务超过 3 个文件或属于数据处理就进入 planned，先让 Claude 展示卡并停下来，再在 plan ready 时唤回 Claude 读计划并重新 run，最后才终验。很多已获授权、范围清楚的任务因此至少多一次 Claude 中途介入；长任务还有周期性 status 阅读要求。最终还要求 Claude 更新两个项目记录文件，超出了“≤20 行卡 + 最终验收”的最小职责。planned 只用 plan.md 是否存在判断下一阶段，并没有让额外的人类轮次形成可靠的状态边界。

   **修法：** 默认把计划作为后台第一阶段，由另一个执行器先审计划，再自动实现；仅在目标、数据写入权限或不可逆操作存在实质歧义时升交 Claude/用户。取消纯文件数和预计时长触发的强制停顿，以及无变化时的周期性 Claude 查询。执行器准备简短验收记录草稿，Claude 终验后只确认必要内容。

   **可删的过度设计：** 删除独立的 planned “落盘后退出再启动”控制流，合并 provider 切换/会话恢复/格式修复中重复的执行与超时处理；删除只 add 从不读取的 used 集合。保留 quick、三轮上限、短摘要和按角色保存会话，这些有明确收益。不要为此再引入通用调度框架或复杂插件层。

   **测试缺口：** 用调用计数验证标准任务无需中途 Claude 轮次，规划/检查/审查失败能自动修复，只有明确阻塞才输出 NEEDS_INPUT；“省 Claude”应作为可验证的流程约束，而不是文案承诺。

已检查且没有发现独立问题的部分：只依赖 Python 标准库；内部修复循环 range(3) 确实限制为首次实现加最多两次修复；check 失败时删除旧 review，避免把上轮 verdict 当作新检查结果；verdict 首行只接受精确 PASS/FAIL；会话按 builder/reviewer 和 provider 分开保存；UTF-8 的受控假执行器日志及 emoji 场景通过。本机 Codex help 也确认当前代码使用的 --approve-for-me、--json、-o 和 resume 的 -c/-m 参数确实存在。以上只确认这些局部行为，不抵消前述边界问题。

验证边界：没有启动真实 agy/Codex 模型、没有改全局 CLI 配置、没有对用户仓库执行 reset/clean/checkout，也没有验证实际云端额度错误格式。复现中的 Git 修改和进程均属于临时测试环境；仓库代码保持不变。

