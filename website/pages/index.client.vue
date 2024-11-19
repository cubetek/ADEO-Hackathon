<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from "vue";
import { Socket } from "socket.io-client";

// Allowed file types for validation
const allowedFileTypes = [
  "application/pdf",
  "application/msword",
  "text/csv",
  "text/plain",
  "image/png",
  "image/jpeg",
];

// Define Types
interface Attachment {
  type: string; // 'image', 'file', or 'link'
  url?: string;
  text?: string;
  image?: string | null;
  summary?: string;
  tags?: string[];
}

interface Message {
  type: "sent" | "received" | "separator";
  text: string;
  time: string;
  attachments: Attachment[];
}

interface Conversation {
  id: number;
  user: {
    name: string;
    photo: string;
    role: string;
    bio: string;
    age: number;
    location: string;
  };
  messages: Message[];
}

interface Prompt {
  title: string;
  description: string;
}

// State variables
const conversations = ref<Conversation[]>([
  {
    id: 1,
    user: {
      name: "Jane Smith",
      photo: "/img/avatars/11.svg",
      role: "Marketing Manager",
      bio: "Loves connecting with people and driving brand success.",
      age: 34,
      location: "New York, NY",
    },
    messages: [{
      type: "received",
      text: "ملاحظة : يجب التاكد من تنزيل النموذج من خلال اتباع تعليمات انزال النموذج و الاستجابه تعتمد على اداء الجاهز",
      time: "10:00 AM",
      attachments: [],
    }],
  },
]);

const { $chatSocket } = useNuxtApp() as unknown as {
  $chatSocket: Socket;
};

const mobileOpen = ref(false);
const loading = ref(false);
const activeConversation = ref(1);
const attachedFiles = ref<{ file: File; preview: string | null }[]>([]);
const fileInputRef = ref<HTMLInputElement | null>(null);
const errorMessage = ref("");
const message = ref(""); // To store the text input
const messageLoading = ref(false);
const chatEl = ref<HTMLElement | null>(null); // Chat container for scrolling
const showPromptInput = ref(false); // Controls prompt input visibility
const newPromptTitle = ref(""); // Title of the new prompt
const newPromptDescription = ref(""); // Description of the new prompt
const prompts = ref<Record<number, Prompt[]>>({}); // Prompts by conversation
const selectedPrompt = ref<Prompt | null>(null); // Stores the selected prompt
const attachedPrompts = ref<Prompt[]>([]); // To handle multiple attached prompts
const uploadingFiles = ref(false);

// Computed for selected conversation
const selectedConversation = computed(() => {
  return conversations.value.find(
    (conversation) => conversation.id === activeConversation.value
  );
});

const currentPrompts = computed(() => {
  return prompts.value[activeConversation.value] || [];
});

// Scroll to the bottom of the chat
function scrollToBottom(smooth = true) {
  nextTick(() => {
    if (chatEl.value) {
      chatEl.value.scrollTo({
        top: chatEl.value.scrollHeight,
        behavior: smooth ? "smooth" : "auto",
      });
    }
  });
}



// Remove attached file
function removeAttachedFile(index: number) {
  const file = attachedFiles.value[index];
  if (file.preview) {
    URL.revokeObjectURL(file.preview);
  }
  attachedFiles.value.splice(index, 1);
}

// File upload handler with FormData
async function handleFileUpload(event: Event) {
  const maxFileSize = 5 * 1024 * 1024; // 5 MB
  const target = event.target as HTMLInputElement;

  if (target.files) {
    for (const file of Array.from(target.files)) {
      if (!allowedFileTypes.includes(file.type)) {
        errorMessage.value = `Unsupported file type: ${file.name}`;
        continue;
      }

      if (file.size > maxFileSize) {
        errorMessage.value = `File "${file.name}" exceeds the size limit.`;
        continue;
      }

      attachedFiles.value.push({
        file,
        preview: file.type.startsWith("image/")
          ? URL.createObjectURL(file)
          : null,
      });
    }

    // Clear file input
    if (fileInputRef.value) {
      fileInputRef.value.value = "";
    }
  }
}
// Submit a new message with FormData upload
async function submitMessage() {
  if (messageLoading.value) return;

  if (!message.value.trim() && attachedFiles.value.length === 0 && !selectedPrompt.value) {
    errorMessage.value = "Cannot send an empty message.";
    return;
  }

  messageLoading.value = true;

  const hasFiles = attachedFiles.value.length > 0;
  const messageText = message.value.trim();
  const promptMessage = selectedPrompt.value ? selectedPrompt.value.description : ""; // Add the prompt message
  try {
    let attachments = [];

    if (hasFiles) {
      // Prepare FormData for files
      const formData = new FormData();
      formData.append("text", messageText);

      attachedFiles.value.forEach(({ file }) => {
        formData.append("files", file);
      });

      // Call the file upload endpoint
      const response = await fetch("http://0.0.0.0:8000/api/v1/uploadfile/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text(); // Capture backend error message
        console.error("Server response:", errorText);
        throw new Error("File upload failed.");
      }

      const responseData = await response.json();
      console.log("File upload response:", responseData);

      // Prepare attachments from API response
      attachments = responseData.files.map((file: any) => ({
        type: "file",
        text: file.file_name,
        status: file.status,
        file_name: file.file_name,
        file_id: file.file_id,
        url: file.url,
        extracted_text: file.extracted_text,
      }));
    }

    // Construct new message
    const newMessage: Message = {
      type: "sent",
      text: messageText,
      time: new Date().toLocaleTimeString(),
      attachments,
    };

    // Update local conversation
    const conversation = selectedConversation.value;
    if (conversation) {
      conversation.messages.push(newMessage);
    }

    // Emit sendMessage event via socket
    $chatSocket.emit("sendMessage", {
      conversationId: activeConversation.value,
      message: {
        text: newMessage.text,
        attachments: newMessage.attachments,
      },
      prompt: promptMessage, // Add the prompt message to the payload
    });

    // Clear the selected prompt after sending
    selectedPrompt.value = null;
  } catch (error) {
    console.error("Error during message submission:", error);
    errorMessage.value = "Failed to send the message. Please try again.";
  } finally {
    resetMessageForm();
  }
}



// Reset form after submission
function resetMessageForm() {
  message.value = "";
  attachedFiles.value.forEach((file) => {
    if (file.preview) {
      URL.revokeObjectURL(file.preview);
    }
  });
  attachedFiles.value = [];
  messageLoading.value = false;
  scrollToBottom();
}

// Select a conversation
function selectConversation(id: number) {
  activeConversation.value = id;
  scrollToBottom();
}

// Add new conversation
function addNewConversation() {
  const newId = conversations.value.length + 1;
  conversations.value.push({
    id: newId,
    user: {
      name: `User ${newId}`,
      photo: "/img/avatars/default.svg",
      role: "New Role",
      bio: "",
      age: 0,
      location: "",
    },
    messages: [],
  });
  activeConversation.value = newId;
  scrollToBottom();
}

// Prompt-related functions
function addPrompt() {
  showPromptInput.value = true;
}

function savePrompt() {
  if (!newPromptTitle.value || !newPromptDescription.value) return;

  if (!prompts.value[activeConversation.value]) {
    prompts.value[activeConversation.value] = [];
  }

  prompts.value[activeConversation.value].push({
    title: newPromptTitle.value.trim(),
    description: newPromptDescription.value.trim(),
  });

  newPromptTitle.value = "";
  newPromptDescription.value = "";
  showPromptInput.value = false;
}

// Lifecycle hooks
onMounted(() => {
  $chatSocket.on("newMessage", (data) => {
    const conversation = conversations.value.find(
      (c) => c.id === data.conversationId
    );
    if (conversation) {
      conversation.messages.push({
        type: "received",
        text: data.message.text,
        time: new Date().toLocaleTimeString(),
        attachments: data.message.attachments || [],
      });
      scrollToBottom();
    }
  });

  $chatSocket.on("error", (error) => {
    console.error("Socket error:", error);
    errorMessage.value = "An error occurred with the chat. Please try again.";
  });
});

// Deselect a prompt
function deselectPrompt() {
  selectedPrompt.value = null;
}

// Select a prompt
function selectPrompt(prompt: Prompt) {
  selectedPrompt.value = prompt;
}

</script>


<template>
  <div class="text-muted-800 h-screen antialiased" dir="rtl">
    <!--Header-->
    <div
      class="ltablet:z-30 border-muted-200 dark:border-muted-800 dark:bg-muted-950 relative flex h-16 w-full items-center justify-between border-b bg-white px-4 lg:z-30"
      :class="mobileOpen ? 'z-20' : 'z-30'"
    >
      <div class="flex w-1/2 items-center gap-2 sm:w-1/5">
        <!-- Hamburger -->
        <button
          class="ltablet:hidden relative flex size-10 items-center justify-center lg:hidden"
          @click="mobileOpen = !mobileOpen"
        >
          <div
            class="start-6 top-1/2 block w-4 -translate-x-1/2 -translate-y-1/2"
          >
            <span
              class="text-primary-500 absolute block h-0.5 w-6 bg-current transition duration-500 ease-in-out"
              :class="mobileOpen ? 'rotate-45' : '-translate-y-2'"
            />
            <span
              class="text-primary-500 absolute block h-0.5 w-5 bg-current transition duration-500 ease-in-out"
              :class="mobileOpen ? 'opacity-0' : ''"
            />
            <span
              class="text-primary-500 absolute block h-0.5 w-6 bg-current transition duration-500 ease-in-out"
              :class="mobileOpen ? '-rotate-45' : 'translate-y-2'"
            />
          </div>
        </button>
        <NuxtLink
          to="https://cubetek.ai/"
          class="ltablet:flex hidden items-center gap-2 lg:flex"
          aria-label="Go to Tairo homepage"
        >
          <CubeLogoText class="text-primary-500 h-6 dark:text-white" />
        </NuxtLink>
      </div>
    </div>
    <!--Wrapper-->
    <div
      class="relative z-20 flex h-[calc(100dvh_-_64px)] w-full flex-row overflow-x-hidden"
    >
      <!--Conversations sidebar-->
      <div
        class="ltablet:static ltablet:py-4 dark:bg-muted-900 ltablet:dark:bg-muted-950 lg:dark:bg-muted-950 fixed start-0 top-0 z-30 flex h-full w-72 shrink-0 flex-col bg-white ps-4 transition-transform duration-300 lg:static lg:py-4"
        :class="
          mobileOpen
            ? 'translate-x-0'
            : '-translate-x-full ltablet:translate-x-0 lg:translate-x-0'
        "
      >
        <!--Mobile header-->
        <div
          class="ltablet:hidden flex h-16 items-center justify-between pe-4 lg:hidden"
        >
          <NuxtLink
            to="/"
            class="flex items-center gap-2"
            aria-label="Go to Tairo homepage"
          >
            <CubeLogo class="text-muted-800 h-9 dark:text-white" />
            <CubeLogoText class="text-muted-800 h-3 dark:text-white" />
          </NuxtLink>
          <UButton
            rounded="lg"
            @click="mobileOpen = false"
          />
        </div>
        <div class="ltablet:pe-0 flex h-full flex-col pe-2 lg:pe-0">
          <!--New conversation-->
          <!-- New conversation button -->
          <div class="flex h-20 items-center justify-center pe-2">
            <UButton
              rounded="full"
              color="primary"
              class="w-full"
              @click="addNewConversation"
            >
              <Icon name="lucide:plus" class="size-4" />
              <span>New Conversation</span>
            </UButton>
          </div>

          <!--Conversations list-->
          <div
            class="nui-slimscroll flex h-[calc(100dvh_-_160px)] flex-col space-y-1 overflow-y-auto pe-2"
          >
            <button
              v-for="conversation in conversations"
              :key="conversation.id"
              class="flex items-center gap-2 rounded-xl p-2 transition-colors duration-200 ease-in-out"
              :class="
                activeConversation === conversation.id
                  ? 'bg-primary-500/10'
                  : 'hover:bg-muted-100 dark:hover:bg-muted-900'
              "
              @click.prevent="selectConversation(conversation.id)"
            >
              <UAvatar :src="conversation.user.photo" />
              <div
                size="sm"
                :class="
                  activeConversation === conversation.id
                    ? 'text-primary-500'
                    : 'text-muted-500 dark:text-muted-400'
                "
              >
                {{ conversation.user.name }}
              </div>
              <span
                class="bg-primary-500 me-3 ms-auto block size-2 rounded-full transition-opacity duration-300"
                :class="
                  activeConversation === conversation.id
                    ? 'opacity-100'
                    : 'opacity-0'
                "
              />
            </button>
          </div>
        </div>
      </div>

      <!--Chat body-->
      <div
        class="dark:bg-muted-950 flex h-full flex-auto flex-col bg-white p-4"
      >
        <div
          class="bg-muted-100 dark:bg-muted-900 flex h-full flex-auto shrink-0 flex-col overflow-hidden rounded-2xl"
        >
          <div class="relative flex h-full flex-col">
            <div
              ref="chatEl"
              class="relative flex h-full flex-col px-4 pb-24 pt-12"
              :class="
                loading ? 'overflow-hidden' : 'overflow-y-auto nui-slimscroll'
              "
            >
              <!-- Loader-->
              <div
                class="bg-muted-100 dark:bg-muted-900 pointer-events-none absolute inset-0 z-10 size-full p-8 transition-opacity duration-300"
                :class="
                  loading ? 'opacity-100' : 'opacity-0 pointer-events-none'
                "
              >
                <!-- Loader content remains unchanged -->
              </div>
              <!-- Messages loop -->
              <div v-if="!loading" class="space-y-12">
                <div
                  v-for="(item, index) in selectedConversation?.messages"
                  :key="index"
                  class="relative flex w-full gap-4"
                  :class="[
                    item.type === 'received' ? 'flex-row' : 'flex-row-reverse',
                  ]"
                >
                  <template v-if="item.type !== 'separator'">
                    <div class="shrink-0">
                      <UAvatar
                        v-if="item.type === 'received'"
                        :src="selectedConversation?.user.photo"
                        size="xs"
                      />
                      <UAvatar
                        v-else-if="item.type === 'sent'"
                        src="/img/avatars/2.svg"
                        size="xs"
                      />
                    </div>
                    <div class="flex max-w-md flex-col">
                      <!-- Message dialog -->
                      <div
                        v-if="item.text.trim()"
                        class="text-muted-800 dark:text-muted-200 rounded-xl p-4"
                        :class="[
                          item.type === 'received'
                            ? 'bg-muted-200 dark:bg-muted-950 rounded-ss-none'
                            : 'bg-primary-500/20 rounded-se-none',
                        ]"
                      >
                      <MDC :value="item.text" tag="article" />
                      </div>

                      <!-- Attachments -->
                      <div
                        v-if="item.attachments.length > 0"
                        class="mt-2 space-y-2"
                      >
                        <template
                          v-for="(attachment, idx) in item.attachments"
                          :key="idx"
                        >
                          <div
                            v-if="attachment.type === 'file'"
                            class="dark:bg-muted-800 max-w-xs rounded-2xl bg-white p-2 flex flex-col"
                            :class="item.type === 'sent' ? 'ms-auto' : ''"
                          >
                            <div class="flex items-center">
                              <Icon
                                name="lucide:file"
                                class="size-5 text-muted-500"
                              />
                              <NuxtLink
                                :to="attachment.url"
                                class="ml-2 text-sm text-blue-500 hover:underline"
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {{ attachment.text }}
                              </NuxtLink>
                            </div>
                            <!-- Display summary and tags only for received messages -->
                            <div v-if="item.type === 'received'" class="mt-1">
                              <div
                                v-if="attachment.summary"
                                class="text-sm text-muted-500"
                              >
                                <p class="font-sans">
                                  {{ attachment.summary }}
                                </p>
                              </div>
                              <div
                                v-if="
                                  attachment.tags && attachment.tags.length > 0
                                "
                                class="mt-1"
                              >
                                <span
                                  v-for="(tag, index) in attachment.tags"
                                  :key="index"
                                  class="inline-block bg-muted-200 dark:bg-muted-700 text-muted-800 dark:text-white text-xs font-sans rounded-full px-2 py-1 mr-1"
                                >
                                  {{ tag }}
                                </span>
                              </div>
                            </div>
                          </div>
                        </template>
                      </div>

                      <!-- Time (moved below the dialog and attachments) -->
                      <div
                        class="text-muted-400 mt-1 font-sans text-xs"
                        :class="item.type === 'received' ? 'text-end' : ''"
                      >
                        {{ item.time }}
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
            <!-- Message Composer -->
            <div class="absolute inset-x-0 bottom-4 w-full px-4">
              <form
                method="POST"
                action=""
                class="dark:bg-muted-950 flex flex-col gap-2 rounded-xl bg-white px-3 py-2"
                @submit.prevent="submitMessage"
              >
                <!-- Attached Prompt -->
                <div v-if="selectedPrompt" class="mb-2">
                  <div
                    class="flex items-center justify-between bg-muted-200 dark:bg-muted-800 p-2 rounded-lg"
                  >
                    <div>
                      <h4
                        class="text-sm font-semibold text-muted-800 dark:text-muted-100"
                      >
                        {{ selectedPrompt.title }}
                      </h4>
                      <p class="text-xs text-muted-600 dark:text-muted-400">
                        {{ selectedPrompt.description }}
                      </p>
                    </div>
                    <button
                      @click.prevent="deselectPrompt"
                      class="text-red-500 hover:underline text-xs"
                    >
                      Remove
                    </button>
                  </div>
                </div>

                <!-- File Previews -->
                <div
                  v-if="attachedFiles.length > 0"
                  class="flex flex-wrap gap-4 mb-2"
                >
                  <div
                    v-for="(attached, index) in attachedFiles"
                    :key="index"
                    class="relative flex items-center gap-2 bg-muted-100 dark:bg-muted-800 p-2 rounded-md"
                  >
                    <div v-if="attached.preview" class="relative">
                      <img
                        :src="attached.preview"
                        alt="Image Preview"
                        class="h-16 w-16 rounded-md object-cover"
                      />
                      <button
                        @click="removeAttachedFile(index)"
                        class="absolute top-0 right-0 bg-red-500 text-white rounded-full p-1"
                        title="Remove File"
                      >
                        <Icon name="lucide:x" class="size-4" />
                      </button>
                    </div>
                    <div v-else class="flex items-center">
                      <Icon name="lucide:file" class="size-5 text-muted-500" />
                      <span class="text-sm text-muted-700 dark:text-muted-300">
                        {{ attached.file.name }}
                      </span>
                      <button
                        @click="removeAttachedFile(index)"
                        class="text-red-500 hover:text-red-700"
                        title="Remove File"
                      >
                        <Icon name="lucide:x" class="size-4" />
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Message Input -->
                <div class="flex items-center gap-2">
                  <!-- File Upload Button -->
                  <button
                    class="hover:bg-muted-100 dark:hover:bg-muted-900 text-muted-400 hover:text-muted-600 dark:hover:text-muted-200 hidden size-10 items-center justify-center rounded-xl transition-colors duration-200 focus:outline-none sm:flex"
                    @click="$refs.fileInput.click()"
                    type="button"
                  >
                    <Icon name="lucide:paperclip" class="size-5" />
                  </button>
                  <input
                    ref="fileInput"
                    type="file"
                    class="hidden"
                    @change="handleFileUpload"
                    multiple
                  />

                  <div class="w-full">
                    <UInput 
                      v-model="message"
                       id="messageInput"
                      :disabled="messageLoading"
                      rounded="lg"
                      :classes="{ input: 'pe-10' }"
                      placeholder="Write a message..."
                      @keydown.enter.exact="submitMessage"
                    />
                  </div>

                  <UButton
                    type="submit"
                    color="primary"
                    rounded="lg"
                    :disabled="messageLoading"
                  >
                    <span>Send</span>
                    <Icon
                      name="ph:paper-plane-right-duotone"
                      class="!hidden size-5 sm:!block"
                    />
                  </UButton>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!--Chat side (Prompt Area)-->
      <div
        class="dark:bg-muted-950 hidden w-80 shrink-0 flex-col bg-white py-4 pe-8 ps-4 lg:flex"
      >
        <div class="relative flex w-full flex-col">
          <div class="mt-4">
            <div class="flex items-center justify-between">
              <div
                tag="h3"
                size="lg"
                class="text-muted-800 dark:text-muted-100"
              >
                Prompts
              </div>
              <button
                @click="addPrompt"
                class="text-primary-500 text-sm hover:underline"
              >
                + Add Prompt
              </button>
            </div>
            <!-- Input Area -->
            <div v-if="showPromptInput" class="mt-4">
              <UInput 
                v-model="newPromptTitle"
                placeholder="Enter prompt title..."
                class="mb-2"
              />
              <UInput
                v-model="newPromptDescription"
                placeholder="Enter prompt description..."
                class="mb-2 h-full"
              />
              <button
                @click="savePrompt"
                class="mt-2 w-full bg-primary-500 text-white py-2 rounded-lg"
              >
                Save Prompt
              </button>
            </div>
            <!-- Prompt List -->
            <ul class="mt-4 space-y-2">
              <li
                v-for="(prompt, index) in currentPrompts"
                :key="index"
                class="bg-muted-100 dark:bg-muted-900 p-4 rounded-lg flex flex-col justify-between cursor-pointer"
                :class="
                  selectedPrompt === prompt
                    ? 'bg-primary-100 dark:bg-primary-700'
                    : ''
                "
                @click="selectPrompt(prompt)"
              >
                <h4
                  class="text-muted-800 dark:text-muted-200 text-sm font-semibold"
                >
                  {{ prompt.title }}
                </h4>
                <p class="text-muted-600 dark:text-muted-400 text-xs">
                  {{ prompt.description }}
                </p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
