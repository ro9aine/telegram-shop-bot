"use client";

import { useEffect, useState } from "react";

import { browserApi } from "../../lib/http";
import { useTelegramWebAppUser } from "../../lib/use-telegram-webapp-user";

type ProfilePayload = {
  profile?: {
    telegram_user_id: number;
    username: string;
    first_name: string;
    last_name: string;
    photo_url: string;
    phone_number: string;
  };
};

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfilePayload["profile"] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);

    browserApi
      .get<ProfilePayload>("/profile/me/", { signal: controller.signal })
      .then((response) => {
        if (response.status >= 200 && response.status < 300) {
          setProfile(response.data.profile ?? null);
        } else {
          setProfile(null);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setProfile(null);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, []);

  const telegramUser = useTelegramWebAppUser();

  const firstName = profile?.first_name || telegramUser?.firstName || "-";
  const lastName = profile?.last_name || telegramUser?.lastName || "-";
  const photoUrl = profile?.photo_url || telegramUser?.photoUrl || "";

  if (loading) {
    return (
      <main className="page">
        <header className="hero">
          <h1>Profile</h1>
          <p>Loading profile...</p>
        </header>

        <section className="profile-card">
          <div className="profile-photo-wrap">
            <div className="profile-photo profile-photo-skeleton" />
          </div>

          <div className="profile-fields">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div className="profile-field" key={`profile-skeleton-${idx}`}>
                <div className="catalog-skeleton-line profile-skeleton-label" />
                <div className="catalog-skeleton-line profile-skeleton-value" />
              </div>
            ))}
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="hero">
        <h1>Profile</h1>
        <p>Your personal data.</p>
      </header>

      <section className="profile-card">
        <div className="profile-photo-wrap">
          {photoUrl ? <img alt="Profile photo" className="profile-photo" src={photoUrl} /> : <div className="profile-photo profile-photo-empty">?</div>}
        </div>

        <div className="profile-fields">
          <div className="profile-field">
            <span className="profile-label">Name</span>
            <span className="profile-value">{firstName}</span>
          </div>
          <div className="profile-field">
            <span className="profile-label">Surname</span>
            <span className="profile-value">{lastName}</span>
          </div>
          <div className="profile-field">
            <span className="profile-label">Phone</span>
            <span className="profile-value">{profile?.phone_number || "-"}</span>
          </div>
          <div className="profile-field">
            <span className="profile-label">Username</span>
            <span className="profile-value">{profile?.username ? `@${profile.username}` : telegramUser?.username ? `@${telegramUser.username}` : "-"}</span>
          </div>
        </div>
      </section>
    </main>
  );
}
