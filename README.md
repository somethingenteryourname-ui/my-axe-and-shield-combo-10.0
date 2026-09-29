# AegisTitan (Minecraft 1.21.11 Paper plugin)

**Aegis Wall Shield** – `/getshield`
Raise it and a giant energy wall shaped like a shield appears where you look.
Blocks all damage and projectiles coming through it (arrows bounce back), nobody can
walk through it, it's unbreakable, and normal axes can't disable it.
`/shieldsize <width> <height>` or `/shieldsize small|medium|large|huge|massive`

**Titan Cleaver** – `/getaxe`
Netherite axe: Sharpness V, Efficiency V, Unbreaking III, Mending, Fire Aspect II.
Sneak + right click = Titan Slam: a colossal particle axe smashes the ground,
splits it open and sends out a shockwave. Any Aegis Wall near the impact is cut in
half and that player's shield is disabled for a few seconds.
`/axesize <1-10>` or `/axesize normal|big|giant|colossal|mountain` makes the axe,
the cut, the cracked ground and the shockwave bigger. At size 10 the blade splits
the ground in a ~118-block-long chasm that goes all the way down through mountains.
`/axecooldown <seconds>` changes the slam cooldown for everyone (0 = none).

Settings are in `plugins/AegisTitan/config.yml` (`/aegistitan reload`).

## Solid models (resource pack)
With `visuals.solid-models: true` the shield wall, the giant axe and the flying spikes are
solid 3D models instead of particles. Every player needs the **AegisTitan-ResourcePack.zip**
(in `.minecraft/resourcepacks`, or set it as the server resource pack). Set it to `false`
to go back to the particle look. The pack source is in `resourcepack/`.

## Building
Push this repo to GitHub → Actions tab → latest "Build AegisTitan" run →
download the `AegisTitan-plugin` artifact → unzip → put the .jar in `plugins/`.
