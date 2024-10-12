from PyFlyt.gym_envs.quadx_envs.quadx_landing_env import QuadXPreciseLandingEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv

def make_env():
    return QuadXPreciseLandingEnv(
        flight_mode=0,
        flight_dome_size=60.0,
        max_duration_seconds=300.0,
        angle_representation="euler",
        # render_mode='human',
        agent_hz=30,
        vo_noise_level=0.1,
    )

def create_model(num_envs: int, load: bool = False) -> PPO:
    envs = SubprocVecEnv([make_env for _ in range(num_envs)])

    if not load:
        model = PPO(
            policy="MlpPolicy",
            env=envs,
            learning_rate=3e-4,
            n_steps=4096,
            batch_size=128,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            vf_coef=0.5,
            use_sde=True,
            verbose=1,
        )
    else:
        model = PPO.load("ppo_pyflyt", envs)
    
    return model


if __name__ == "__main__":
    model = create_model(15, False)
    
    model.learn(total_timesteps=1_000_000)
    model.save("ppo_pyflyt")



#! Timesteps for number of envs:
#* ~325 timesteps - 1 cores
#* ~575 timesteps - 8 cores
#* ~727 timesteps - 12 cores

#* ~1068 timesteps - 12 cores with oprimizations 45
