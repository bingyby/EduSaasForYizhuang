# Tutor Core — Frappe 分支（未完成的原型）

本目录是独立 Frappe App 的初始代码，**尚不是可运行的 SaaS Demo**。2026-10-30 已通过 GitHub Actions 临时云端环境验证：启动 ERPNext、安装 Education 与 Tutor Core、迁移 12 个 DocType、HTTP 登录页返回成功。测试环境随后销毁；未验证业务功能、UI、权限或生产部署。请勿用于真实数据或生产环境。

## 版本与部署方向

Frappe Education 官方兼容矩阵列出 Education `version-16` 与 Frappe `version-16` 兼容。建议选同一大版本的 Framework、ERPNext、Education 稳定版本并锁定具体 tag/commit；尚未完成三者版本锁定；已在临时 CI 中完成安装冒烟测试。Education 官方安装流程先安装 ERPNext，再安装 Education。见 https://github.com/frappe/education 和 https://github.com/frappe/frappe_docker 。

安装目标（以下为待验证的 Bench 步骤，不是已验证启动命令）：

```bash
# 在具备 Frappe v16 Bench 的环境中，安装 ERPNext 与 Education 后：
bench get-app /path/to/frappe-tutor
bench --site education.test install-app tutor_core
bench --site education.test migrate
bench start
```

`bench get-app` 的本地目录方式及命名应在目标 Bench 环境实测；未提供可直接启动的容器配置。

## 代码与模型

`pyproject.toml`、`tutor_core/hooks.py` 为应用入口，`tutor_core/tutor_core/doctype/` 包含 12 个初始 DocType 元数据。`tutor_core/domain.py` 实现纯函数的每周日期生成和按分钟计算金额；`tests/` 是对应的独立 Python 测试。DocType 定义已在此次 v16 安装中迁移；UUID 生成及业务行为尚未验证。

```mermaid
erDiagram
    STUDENT ||--o{ TUTOR_CONTRACT : signs
    INSTRUCTOR ||--o{ TUTOR_CONTRACT : teaches
    TUTOR_CONTRACT ||--o{ RECURRING_LESSON : schedules
    RECURRING_LESSON ||--o{ LESSON_SESSION : generates
    LESSON_SESSION ||--o| BILLING_RECORD : bills
    LESSON_SESSION ||--o{ LESSON_CHANGE : changes
    LESSON_SESSION ||--o{ LESSON_SUMMARY : documents
    TUTOR_CONTRACT ||--o{ TUTOR_RATE : prices
```

Education 的 Student、Instructor、Course、Guardian 和 Fee 应评估复用；课程实例、单次变更、合同、费率、结算、进度记录和事务 outbox 需要 Tutor Core 开发。User、Role、权限、版本审计、File、通知、REST、Webhooks 和后台任务可利用 Frappe 能力；会计、Employee 和 CRM 应按实际需要复用 ERPNext/相关开源应用，不能声称已经接通。

## 关键未完成工作

- 已有管理员限定的周期课次生成及防重初版，缺少冲突检测、调课审计和并发压力验证；单次修改不得更改周期规则。
- 管理员完成课次时可生成费率快照；无匹配或多重匹配费率时拒绝完成。尚缺完整费率区间校验、财务更正流程及并发压力验证。
- 当前 DocType 仅 System Manager 有权限，教师、学生、监护人和机构级 RBAC 尚未实现或测试。不能上线；不能把客户端过滤当安全边界。需要逐项测试列表、单条读取、REST、附件与写入。
- 没有教师仪表盘、日历、学生详情、学生门户、演示数据或截图。
- Outbox DocType 仅为占位，缺少事务内事件写入、版本递增、投递、重试、死信、幂等和消费端去重；没有与知识图谱的连接。事件契约计划包含 lesson.created/updated/completed/cancelled、student.created/updated、lesson_summary.created/updated，带 event_id、event_type、entity_id、entity_version、occurred_at、tenant_id。业务系统保留事实所有权。
- 无真实负载测试、用户规模验证、部署自动化、备份恢复方案。开源复用比例无法客观量化，当前未实测集成，不能给出有依据的百分比。

## 多租户方向

建议商业化初期采用 site-per-tenant：每机构独立站点与数据库，借助 Frappe 原生多站点减少跨租户数据泄漏风险，但要承担站点生命周期、升级、备份和运维成本。单站点 organization_id 可降低站点数量，却需要在所有 DocType、REST、附件、后台任务、报表和搜索上完整执行行级隔离；本原型并未实现这种隔离。超大客户或合规要求不同的客户可单独部署；容量需压测，100–1000 教师、10000+ 学生不是已验证指标。

## 许可证

此原型计划以 GPL-3.0-or-later 提供；Frappe Framework、ERPNext、Education 各自的仓库许可证及具体版本、组合与分发方式必须逐项核查。GPL 通常要求分发衍生作品时满足相应源代码和许可证义务，普通 GPL 与 AGPL 的网络使用条款不同；SaaS 架构、定制及交付是否触发义务应结合实际由律师判断，此处不是法律意见。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

纯 Python 测试覆盖计算边界；GitHub Actions 还在临时站点测试了课程生成、重复生成、账单快照和重复完成。尚未验证并发、权限隔离和完整生产部署。
