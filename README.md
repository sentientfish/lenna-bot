# lenna-bot
Lenna can now assist Shikikan in Discord!

Lenna listens and responds with information about dolls, weapons, and others!

Lenna is always looking to improve, so there may be more ways that Lenna can help in the future!

## User Notes
Before deploying Lenna as a discord bot, **please initialize the `headers.json` file with appropriate credentials**

This will not only help identify bot queries, but also a respectful courtesy that should be upheld.

Please also refrain from using too many force commands to repeatedly query the IOPWIKI. Local caching was intentionally implemented to prevent
the IOPWIKI from being overloaded with too many queries.

Please remain respectful of this, so we may all continue using information provided by the wiki!

## Commands
Currently, Lenna will listen for the following commands:

| *No.* | *Command*                         | *Description*                                                                                                 |
| ----- | --------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 01    | !help                             | Help function to show what commands are available                                                             |
| 01    | !bingo                            | (Pseudo-)Randomly sends Lenna's or Leva's bingo video! very cute!!!                                           |
| 02    | !echo                             | Lenna will repeat what Shikikan says!                                                                         |
| 03    | !doll <doll_name>                 | Looks up doll information given a doll name and posts it as an embed                                          |
| 04    | !mdoll <doll_name>                | Looks up doll information given a doll name and posts it as an embed, forcefully using cache                  |
| 05    | !fdoll <doll_name>                | Looks up doll information given a doll name and posts it as an embed, forcefully quering wiki                 |
| 06    | !keys <doll_name>                 | Looks up a doll's neural key information given a doll name and posts it as an embed                           |
| 07    | !fkeys <doll_name>                | Looks up a doll's neural key information given a doll name and posts it as an embed, forcefully quering wiki  |
| 08    | !weapon <weapon_name>             | Looks up weapon information given a weapon name and posts it as an embed                                      |
| 09    | !mweapon <weapon_name>            | Looks up weapon information given a weapon name and posts it as an embed, forcefully using cache              |
| 10    | !fweapon <weapon_name>            | Looks up weapon information given a weapon name and posts it as an embed, forcefully quering wiki             |
| 11    | !define <status_effect_name>      | Looks up status effect information given a status effect name and posts it as an embed                        |

### Examples
`!bingo`

`!echo hello!`

`!doll makiatto`

`!doll mAKiATTo`

`!weapon bittersweet caramel`

`!define frozen`

`!define acid corrosion ii`

## Force Commands
Commands with that starts with the `f` prefix (e.g., `!fdoll`) requires certain admin privileges. This admin privileges is attached to roles. It is up to the server deploying Lenna to set these role rules. Server owners/admins can set the roles with admin privileges by modifying `data/admin.txt` file. Lines starting with `#` will be ignored.

## Feedback

If you have ideas on how Lenna can further help, please reach out to @aguren on discord! (no promises that your suggestion will be implemented because aguren is very lazy)