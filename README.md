ak4-slack
====
[![test](https://github.com/tfuji384/akashi-slack/actions/workflows/python-app.yml/badge.svg)](https://github.com/tfuji384/akashi-slack/actions/workflows/python-app.yml)

## TL;DR

- Slackからslash commandでAKASHIに打刻するためのAPI

## Demo

![demo](statics/demo.gif)

## Deploy

### SlackApp

- slash commandsの設定
  - slash commandを追加する
  ![slach command 1](statics/slash_commands_1.png)

  - request urlを設定する(パスは`/slash`)
  ![slash command 2](statics/slash_commands_2.png)

- interactivity
  - interactivity & shortcutsを設定する（パスは`/actions`）
  ![interactivity](statics/interactivity.png)

- permissionsを追加
  - `chat:write`, `channels:join`（打刻の通知先を設定しない場合は不要）を追加する
  ![bot user scopes](statics/bot_user_scopes.png)

### Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

- Heroku Schedulerに以下のjobを追加する
  - `curl https://[your-app-name].herokuapp.com/`（Frequency: Every 10 minutes）
  - `python refresh_user_tokens.py`（Frequency: Daily at 6:00 PM UTC）

## Environment Veriables

- AKASHI_COMPANY_ID
- SLACK_BOT_TOKEN
- SLACK_SIGNING_SECRET
- DATABASE_URL
- SLACK_CHANNEL_ID(optional)

## Requirements

- Python3.9+
- Pipenv

## Development

### Installation

- `pipenv install --dev`

### Pipenv scripts

- `pipenv run start`
  run local server
- `pipenv run sort`
  run isort
- `pipenv run test-cov`
  run tests

## License

[MIT](LICENSE)
