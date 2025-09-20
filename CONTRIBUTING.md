# Luna Bot - 開発貢献ガイド

## 貢献について

Lunaプロジェクトへの貢献を歓迎します！バグ報告、機能提案、コード貢献など、あらゆる形での貢献が価値あるものです。

## 貢献の種類

### バグ報告
- 予期しない動作の報告
- エラーメッセージの共有
- 再現手順の提供

### 機能提案
- 新機能のアイデア
- 既存機能の改善提案
- UX/UI改善案

### コード貢献
- バグ修正
- 新機能実装
- パフォーマンス改善
- テストコード追加

### ドキュメント改善
- ドキュメントの修正・更新
- チュートリアル作成
- 翻訳支援

---

## 開発環境セットアップ

### 前提条件

- **Python 3.13以上**
- **Poetry** (依存関係管理)
- **Git**
- **VSCode** (推奨エディタ)

### 環境構築手順

```bash
# 1. リポジトリのフォーク・クローン
git clone https://github.com/your-username/luna-bot.git
cd luna-bot

# 2. 開発ブランチ作成
git checkout -b feature/your-feature-name

# 3. 依存関係インストール
poetry install

# 4. 開発用設定ファイル作成
cp config.toml.example config.dev.toml

# 5. 設定ファイル編集（開発用Bot Token設定）
nano config.dev.toml
```

### VSCode設定

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true
}
```

### 推奨VSCode拡張機能

- Python
- Pylance
- Black Formatter
- Ruff
- Git Graph

---

## 開発ワークフロー

### ブランチ戦略

```
main
├── develop
│   ├── feature/ticket-system-enhancement
│   ├── feature/new-logging-options
│   └── bugfix/memory-leak-fix
└── hotfix/critical-security-patch
```

#### ブランチ命名規則

- `feature/機能名` - 新機能開発
- `bugfix/バグ内容` - バグ修正
- `hotfix/緊急修正内容` - 緊急修正
- `docs/ドキュメント名` - ドキュメント更新

### 開発手順

1. **Issue作成またはアサイン**
2. **ブランチ作成**
3. **実装・テスト**
4. **コミット・プッシュ**
5. **プルリクエスト作成**
6. **コードレビュー**
7. **マージ**

---

## コーディング規約

### Python スタイルガイド

基本的に**PEP 8**に準拠し、以下のツールで自動化：

```bash
# フォーマッター実行
poetry run black .

# リンター実行
poetry run ruff check .

# 型チェック実行
poetry run mypy .
```

### 命名規則

```python
# クラス名: PascalCase
class TicketManager:
    pass

# 関数・変数名: snake_case
def create_ticket():
    user_id = 123

# 定数: SCREAMING_SNAKE_CASE
MAX_TICKETS_PER_USER = 3

# プライベートメソッド: _アンダースコア始まり
def _internal_method():
    pass
```

### docstring規約

```python
def create_ticket(guild_id: int, user_id: int, title: str) -> Ticket:
    """チケットを作成する

    Args:
        guild_id: Discord サーバーID
        user_id: チケット作成者のユーザーID
        title: チケットのタイトル

    Returns:
        作成されたTicketオブジェクト

    Raises:
        ValueError: 無効なパラメータが指定された場合
        DatabaseError: データベース操作に失敗した場合
    """
```

### 型ヒント

```python
from typing import Optional, List, Dict, Any
from discord import Guild, User, TextChannel

async def process_tickets(
    guild: Guild,
    users: List[User]
) -> Dict[int, Optional[TextChannel]]:
    """型ヒントを適切に使用"""
    pass
```

---

## アーキテクチャガイド

### プロジェクト構造の理解

```
luna/
├── bot.py              # メインエントリーポイント
├── config/             # 設定管理
├── database/           # データモデル・DB操作
├── di/                 # 依存性注入コンテナ
├── patterns/           # デザインパターン実装
├── cogs/               # Discord機能モジュール
├── events/             # イベントハンドラー
└── utils/              # ユーティリティ関数
```

### 新機能開発の流れ

1. **データモデル定義** (`database/models.py`)
2. **データベース操作実装** (`database/manager.py`)
3. **Cog実装** (`cogs/新機能.py`)
4. **DIコンテナ更新** (`di/container.py`)
5. **テスト作成** (`tests/`)

### デザインパターンの活用

#### Command Pattern
```python
class TicketCommand:
    def __init__(self, ticket_service):
        self.ticket_service = ticket_service

    async def execute(self):
        # コマンド実行ロジック
        pass

    async def undo(self):
        # 取り消しロジック（必要に応じて）
        pass
```

#### Observer Pattern
```python
# イベント発火
await self.event_bus.emit_event("ticket_created", {
    "ticket_id": ticket.id,
    "user_id": user.id
})

# イベント購読
class TicketObserver:
    async def on_ticket_created(self, event_data):
        # チケット作成時の処理
        pass
```

---

## テスト指針

### テスト構造

```
tests/
├── unit/               # 単体テスト
│   ├── test_models.py
│   ├── test_manager.py
│   └── test_utils.py
├── integration/        # 統合テスト
│   ├── test_cogs.py
│   └── test_database.py
└── fixtures/           # テストデータ
    └── sample_data.py
```

### テスト実行

```bash
# 全テスト実行
poetry run pytest

# カバレッジ付きテスト
poetry run pytest --cov=. --cov-report=html

# 特定テストのみ実行
poetry run pytest tests/unit/test_models.py

# デバッグモードでテスト
poetry run pytest -v -s tests/unit/test_models.py::test_ticket_creation
```

### テスト作成例

```python
import pytest
from datetime import datetime
from database.models import Ticket, TicketStatus

class TestTicketModel:
    def test_ticket_creation(self):
        """チケット作成テスト"""
        ticket = Ticket(
            guild_id=12345,
            channel_id=67890,
            user_id=11111,
            title="テストチケット"
        )

        assert ticket.guild_id == 12345
        assert ticket.status == TicketStatus.OPEN
        assert ticket.created_at is not None

    @pytest.mark.asyncio
    async def test_ticket_close(self):
        """チケットクローズテスト"""
        # テストロジック
        pass
```

### モックとフィクスチャ

```python
@pytest.fixture
async def mock_bot():
    """テスト用Botモック"""
    bot = Mock()
    bot.get_guild.return_value = Mock()
    return bot

@pytest.fixture
def sample_ticket():
    """サンプルチケットデータ"""
    return Ticket(
        guild_id=12345,
        channel_id=67890,
        user_id=11111,
        title="サンプルチケット"
    )
```

---

## プルリクエストガイド

### PR作成前のチェックリスト

- [ ] すべてのテストが通過
- [ ] コードフォーマットが適用済み
- [ ] 型チェックエラーなし
- [ ] ドキュメント更新（必要に応じて）
- [ ] CHANGELOG.md更新

### PRテンプレート

```markdown
## 変更内容

### 概要
-

### 変更点
-
-

## テスト

### テスト項目
- [ ] 単体テスト通過
- [ ] 統合テスト通過
- [ ] 手動テスト実行

### テスト環境
- Python: 3.13
- Discord.py: 2.4.0

## 関連Issue

Closes #123

## 追加注意事項

-
```

### PRレビュー観点

#### 機能面
- 要件を満たしているか
- エラーハンドリングは適切か
- パフォーマンスに問題はないか

#### コード品質
- 可読性・保守性は良いか
- 適切な抽象化がされているか
- セキュリティ問題はないか

#### テスト
- 適切なテストカバレッジがあるか
- エッジケースを考慮しているか

---

## 機能開発ガイド

### 新しいCog作成

```python
# cogs/new_feature.py
import discord
from discord import app_commands
from discord.ext import commands
from di import DatabaseDep, EventBusDep, ConfigDep
from dependency_injector.wiring import inject

class NewFeatureCog(commands.Cog):
    @inject
    def __init__(
        self,
        bot,
        database=DatabaseDep,
        event_bus=EventBusDep,
        config=ConfigDep
    ):
        self.bot = bot
        self.database = database
        self.event_bus = event_bus
        self.config = config

    @app_commands.command()
    async def new_command(self, interaction: discord.Interaction):
        """新しいコマンドの説明"""
        await interaction.response.defer()

        try:
            # 実装ロジック
            result = await self._process_command(interaction)

            embed = discord.Embed(
                title="✅ 成功",
                description="処理が完了しました",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)

            # イベント発火
            await self.event_bus.emit_event("new_command_executed", {
                "user_id": interaction.user.id,
                "guild_id": interaction.guild.id
            })

        except Exception as e:
            self.logger.error(f"Command failed: {e}")
            embed = discord.Embed(
                title="❌ エラー",
                description="処理中にエラーが発生しました",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(NewFeatureCog(bot))
```

### データベースモデル追加

```python
# database/models.py に追加
class NewModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int
    user_id: int
    data: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
```

---

## リリースプロセス

### バージョン管理

セマンティックバージョニング（SemVer）を採用：

- **MAJOR**: 破壊的変更
- **MINOR**: 後方互換性のある機能追加
- **PATCH**: 後方互換性のあるバグ修正

### リリース手順

1. **developブランチでの開発・テスト**
2. **バージョン更新**
   ```bash
   # pyproject.toml のversion更新
   poetry version patch  # or minor, major
   ```
3. **CHANGELOG.md更新**
4. **mainブランチにマージ**
5. **タグ作成・リリース**
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

---

## コミュニティとコミュニケーション

### Issue Discussion

- GitHub Issuesでの議論参加
- 建設的なフィードバック提供
- 他の開発者のサポート

### 質問・サポート

- GitHub Discussions使用
- 詳細な情報提供（エラーログ、環境情報等）
- 既存のIssueやドキュメント確認

### 行動規範

- 敬意を持った対話
- 建設的な批判
- 包括的なコミュニティ作り
- ハラスメント・差別の禁止

---

## 開発ツール・リソース

### 有用なコマンド

```bash
# 開発環境セットアップ
make dev-setup

# テスト実行
make test

# コードフォーマット
make format

# リンター実行
make lint

# 型チェック
make typecheck

# ドキュメント生成
make docs
```

### 参考資料

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [dependency-injector Documentation](https://python-dependency-injector.ets-labs.org/)
- [pytest Documentation](https://docs.pytest.org/)

---

## よくある質問

### Q: 初心者でも貢献できますか？
A: もちろんです！小さなバグ修正やドキュメント改善から始めることをお勧めします。

### Q: どの機能から実装を始めるべきですか？
A: GitHub Issues の "good first issue" ラベル付きIssueから始めることをお勧めします。

### Q: テストの書き方がわからない場合は？
A: 既存のテストファイルを参考にし、不明な点があればIssueで質問してください。

### Q: 大きな機能変更を提案したいのですが？
A: まずGitHub Issuesで提案・議論を行い、コミュニティの合意を得てから実装を始めてください。

---

## 謝辞

Lunaプロジェクトへの貢献を検討いただき、ありがとうございます。皆さんの貢献により、より良いDiscord BOTを作り上げることができます。

何か質問があれば、お気軽にGitHub Issuesで声をかけてください。