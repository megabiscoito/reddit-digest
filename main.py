import sys
import config
from modules.reddit_client import fetch_all_subreddits
from modules.summarizer import generate_summary
from modules.email_sender import send_digest_email


def main():
    config.validate()

    print(f"A recolher posts de: {', '.join(config.SUBREDDITS)}")
    subreddit_data = fetch_all_subreddits(config.SUBREDDITS)
    total_posts = sum(len(d["posts"]) for d in subreddit_data)
    print(f"  {total_posts} posts recolhidos")

    print("A gerar resumo com Gemini...")
    summary = generate_summary(subreddit_data)
    print("  Resumo gerado")

    print("A enviar email...")
    send_digest_email(summary, config.SUBREDDITS)
    print("Concluído.")


if __name__ == "__main__":
    try:
        main()
    except EnvironmentError as e:
        print(f"Erro de configuração: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro: {e}")
        raise
