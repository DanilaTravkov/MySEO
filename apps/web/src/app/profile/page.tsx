import type { Metadata } from "next";

import { PageHeading } from "@/components/page-heading";

import { ProfileWorkspace } from "./profile-workspace";

export const metadata: Metadata = { title: "Profile" };

export default function ProfilePage() {
  return (
    <>
      <PageHeading eyebrow="Account" title="Your profile" description="Manage your personal details, workspace information, and product experience." />
      <ProfileWorkspace />
    </>
  );
}
