package dev.aegistitan;

import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.World;
import org.bukkit.entity.Display;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.Matrix3f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.HashSet;
import java.util.Set;

/**
 * Solid 3D visuals: big item-display entities that use the models in the AegisTitan resource pack.
 * Every model is centred on its entity and 1 block across before scaling.
 */
final class Models {

    static final String NAMESPACE = "aegis";
    static final String WALL = "aegis_wall";
    static final String WALL_LEFT = "wall_broken_left";
    static final String WALL_RIGHT = "wall_broken_right";
    static final String AXE = "titan_axe_giant";
    static final String SPIKE = "titan_spike";

    /** Item displays are drawn turned 180 degrees; this undoes that so our maths stays simple. */
    private static final Quaternionf FLIP = new Quaternionf().rotationY((float) Math.PI);

    private static AegisTitan plugin;
    private static final Set<ItemDisplay> alive = new HashSet<>();

    private Models() {
    }

    static void init(AegisTitan owner) {
        plugin = owner;
    }

    /** true = solid models (needs the resource pack), false = the original particle look. */
    static boolean enabled() {
        return plugin != null && plugin.getConfig().getBoolean("visuals.solid-models", true);
    }

    static ItemStack item(String id) {
        ItemStack stack = new ItemStack(Material.PAPER);
        ItemMeta meta = stack.getItemMeta();
        meta.setItemModel(new NamespacedKey(NAMESPACE, id));
        stack.setItemMeta(meta);
        return stack;
    }

    /** Spawns an invisible (scale ~0) model; call pose() to show it. */
    static ItemDisplay spawn(World world, Vector pos, String id, float viewRange) {
        ItemDisplay display = world.spawn(pos.toLocation(world), ItemDisplay.class, d -> {
            d.setItemStack(item(id));
            d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
            d.setPersistent(false);
            d.setBrightness(new Display.Brightness(15, 15));
            d.setViewRange(viewRange);
            d.setShadowRadius(0f);
            d.setShadowStrength(0f);
            d.setTeleportDuration(2);
            d.setTransformation(new Transformation(new Vector3f(), new Quaternionf(),
                    new Vector3f(0.001f, 0.001f, 0.001f), new Quaternionf(FLIP)));
        });
        alive.add(display);
        return display;
    }

    static void remove(ItemDisplay display) {
        if (display != null) {
            alive.remove(display);
            if (display.isValid()) {
                display.remove();
            }
        }
    }

    /** Removes every model (used when the plugin shuts down). */
    static void removeAll() {
        for (ItemDisplay d : alive) {
            if (d.isValid()) {
                d.remove();
            }
        }
        alive.clear();
    }

    /** A rotation whose local X, Y and Z axes point along x, y and z (orthonormal, right-handed). */
    static Quaternionf basis(Vector x, Vector y, Vector z) {
        Matrix3f m = new Matrix3f(
                (float) x.getX(), (float) x.getY(), (float) x.getZ(),
                (float) y.getX(), (float) y.getY(), (float) y.getZ(),
                (float) z.getX(), (float) z.getY(), (float) z.getZ());
        return new Quaternionf().setFromNormalized(m).normalize();
    }

    /**
     * Places a model so that the point {@code pivot} (in the model's own -0.5..0.5 space, before scaling)
     * sits at the entity's position plus {@code offset}.
     */
    static void pose(ItemDisplay d, Quaternionf rotation, Vector3f scale, Vector3f pivot, Vector offset, int interpolate) {
        if (d == null || !d.isValid()) {
            return;
        }
        Vector3f scaledPivot = new Vector3f(pivot).mul(scale);
        Vector3f rotatedPivot = new Quaternionf(rotation).transform(scaledPivot);
        Vector3f translation = new Vector3f((float) offset.getX(), (float) offset.getY(), (float) offset.getZ()).sub(rotatedPivot);
        d.setInterpolationDelay(0);
        d.setInterpolationDuration(interpolate);
        d.setTransformation(new Transformation(translation, new Quaternionf(rotation), new Vector3f(scale), new Quaternionf(FLIP)));
    }

    /** Moves the entity itself (smoothly, thanks to its teleport duration). */
    static void move(ItemDisplay d, Vector pos) {
        if (d != null && d.isValid()) {
            d.teleport(pos.toLocation(d.getWorld()));
        }
    }
}
