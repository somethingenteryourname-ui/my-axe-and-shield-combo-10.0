package dev.aegistitan;

import org.bukkit.command.PluginCommand;
import org.bukkit.plugin.PluginManager;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.List;

public final class AegisTitan extends JavaPlugin {

    private Terrain terrain;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        updateConfig();

        Models.init(this);
        Items items = new Items(this);
        terrain = new Terrain(this);
        WallManager walls = new WallManager(this, items);
        TitanAxe axe = new TitanAxe(this, items, walls, terrain);

        PluginManager pm = getServer().getPluginManager();
        pm.registerEvents(walls, this);
        pm.registerEvents(terrain, this);
        pm.registerEvents(axe, this);
        walls.start();

        Commands commands = new Commands(this, items, walls, axe);
        for (String name : List.of("getshield", "shieldsize", "getaxe", "axesize", "axecooldown", "aegistitan")) {
            PluginCommand cmd = getCommand(name);
            if (cmd != null) {
                cmd.setExecutor(commands);
                cmd.setTabCompleter(commands);
            }
        }
        getLogger().info("AegisTitan ready: /getshield, /shieldsize, /getaxe, /axesize, /axecooldown");
    }

    /**
     * Adds any new settings to an existing config.yml and moves old, laggy limits down to the new safer ones,
     * so nobody has to delete their config after an update.
     */
    private void updateConfig() {
        getConfig().options().copyDefaults(true);
        int version = getConfig().getInt("config-version", 1);
        if (version < 3) {
            getConfig().set("axe.blocks-per-tick", Math.min(getConfig().getInt("axe.blocks-per-tick", 2500), 2500));
            getConfig().set("config-version", 3);
        }
        if (getConfig().getInt("config-version", 1) < 4) {
            getConfig().set("trident", null); // the trident was removed
            getConfig().set("config-version", 4);
        }
        saveConfig();
    }

    @Override
    public void onDisable() {
        Models.removeAll();
        if (terrain != null) {
            terrain.restoreAll();
        }
    }
}
